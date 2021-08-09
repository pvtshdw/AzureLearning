from azureQueries import * # File with our queries
from az.cli import az # Wrapper for the Azure CLI commands
from datetime import date, datetime, timedelta# Date/Time - Again, duh
from io import StringIO # Used to buffer output to memory
import json # JSON - Duh
from time import sleep # Pause execution before retrying a query

# ----------------------------------------
# Configure application settings
# ----------------------------------------
# The Log Analytics workspace ID
workspaceId = "<Workspace ID>"

# Start and end dates for the export (YYYY, M, D)
# NOTE: If running more than one concurrent export you MUST stagger start dates
#   E.G. VM 1 start 2021-07-30
#        VM 2 start 2021-07-31
#        VM 3 start 2021-08-01
startDate = date(2020, 12, 4)
endDate = date(2021, 5, 5)

# Number of VMs exporting data
concurrentExports = 4

# Maximum number of times to re-try a query
maxRetryCount = 10

# Pause time between retries
sleepTimeSeconds = 30

# Location to write exported data
outputDirectory = "./data"

# Maximum size of returned data (API limit of 64MB)
maxResponseSize = 60000000 # Gives us 4MB buffer for JSON formatting and such

# Maximum number of rows per file (to limit file size)
maxRowsPerFile = 350000000 # Should keep us ~500MB

# Set which query we want to execute to get the tables to export
#tablesToExportQuery = getTableRowCountsByHour
#tablesToExportQuery = getFilteredSyslogRowCount # Syslog
tablesToExportQuery = getSecurityEventRowCountsByHour # SecurityEvent

# Set the query to export the data
#dataExportQuery = getTableData
#dataExportQuery = getSyslogData # Syslog
dataExportQuery = getSecurityEventData # SecurityEvent

# ----------------------------------------
# Configure logging
# ----------------------------------------
import logging
logger = logging.getLogger('archiveSentinelData') # This only displays entries from this app
# logger = logging.getLogger() # Use this to get log info from Az.CLI
logger.setLevel(logging.DEBUG) # Set the default logging level

# Create a logging file handler
fh = logging.FileHandler(f'{logger.name}.{datetime.now().date()}.log')
fh.setLevel(logging.DEBUG)

# Create a console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# Add the handlers to the logging class
logger.addHandler(fh)
logger.addHandler(ch)

# ----------------------------------------
# Create the data directory if it does not exist
# ----------------------------------------
import os
if not os.path.exists('data'):
    os.makedirs('data')

logger.info('------------------------------ START ------------------------------')
try:
    # ----------------------------------------
    # Loop through each day
    # ----------------------------------------
    currentDay = startDate
    while currentDay <= endDate:
        logger.info(f'---------->> Exporting data for {currentDay} <<----------')
        # ----------------------------------------
        # Get record counts for the data sources
        # ----------------------------------------
        logger.debug('[--] Replace the variables in the query to get number of rows per table per hour')
        query1 = tablesToExportQuery.replace("STARTDATE", str(currentDay))
        logger.debug(f'[--] {query1}')

        logger.info('[**] Query the workspace to get the list of tables to export')
        exitCode, queryResults, logs = az(f'monitor log-analytics query --workspace {workspaceId} --analytics-query "{query1}"')

        if (exitCode == 0):
            # ----------
            # Iterate through each table to be exported
            # ----------
            for i, queryResult in enumerate(queryResults):
                # The results come in with single quotes, so replace those
                r = repr(queryResult).replace("'", '"')
                # Load the query results in to a JSON object
                tableInfo = json.loads(r)

                logger.debug('[--] Format a time stamp for the file name')
                timestamp = datetime.strptime(tableInfo["TimeGenerated"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d_%H%M")
                
                # Initialize a counter for the file rotation
                filenumber = 1

                logger.debug('[--] Set the number of records to fetch per call')
                totalRowCount = int(tableInfo["RowCount"])
                
                # Calculate the number of records to fetch rounded down to the nearest hundred
                rowsToFetch = int(round(maxResponseSize / int(tableInfo["SizePerEntry"]), -2))

                logger.debug('[--] Figure out roughly how many entries will fit in a 1GB file')
                logger.debug(f'[--] SizePerEntry = {tableInfo["SizePerEntry"]}')
                entriesPerFile = maxRowsPerFile / int(tableInfo["SizePerEntry"])
                logger.debug(f'[--] Entries per file = {entriesPerFile}')

                logger.debug(f'[--] Row Count = {totalRowCount}')
                logger.debug(f'[--] Fetch {rowsToFetch} for table {tableInfo["TableName"]}')

                logger.info(f'[**] For {tableInfo["TimeGenerated"]}, {tableInfo["TableName"]} has {tableInfo["RowCount"]} rows and can fetch {rowsToFetch} entries per call')

                # Initialize the string buffer to hold the data
                outputString = StringIO()
                
                # Initialize the tries counter
                tries = 0

                currentFetchCount = 1
                while currentFetchCount < totalRowCount:
                    logger.debug('[--] Replace the variables in the query')
                    query = dataExportQuery.replace("TABLENAME", tableInfo["TableName"])
                    query = query.replace("STARTTIME", tableInfo["TimeGenerated"])
                    query = query.replace("STARTINDEX", str(currentFetchCount))
                    query = query.replace("ENDINDEX", str(currentFetchCount + rowsToFetch - 1))

                    logger.debug(f'[--] Query:\n{query}')

                    logger.info(f'[**] Query Start ({tableInfo["TableName"]}:{tableInfo["TimeGenerated"]}:{currentFetchCount})')
                    exitCode, tableResults, logs = az(f'monitor log-analytics query --workspace {workspaceId} --analytics-query "{query}"')
                    logger.info(f'[**] Query End')
                    
                    rowsReturned = len(tableResults)
                    logger.debug(f'[--] {rowsReturned} records returned')
                    if (exitCode == 0):
                        logger.debug('[--] Write results to the buffer')
                        currentRow = 1
                        for row in tableResults:
                            if currentRow < rowsReturned:
                                # outputString.write(f'{str(formattedRow)},\n')
                                outputString.write(f'{json.dumps(row)},\n')
                            else:
                                # outputString.write(f'{str(formattedRow)}\n')
                                outputString.write(json.dumps(row))
                            #end if
                            currentRow += 1
                        #end for

                        logger.debug('[--] Reset the number of tries after every successful query')
                        tries = 0
                    else:
                        logger.warning(f'[!!] Error fetching {rowsToFetch} rows from {tableInfo["TableName"]} starting at row number {currentFetchCount}\n\t Exit code:{exitCode}\n\t Log Message: {logs}')

                        # Increment the tries counter
                        tries += 1

                        # If we have hit the maximum number of retries, bail out
                        if (tries >= maxRetryCount):
                            logger.error('[!!] Maximum tries reached')
                            raise Exception(f'{logs}')
                        #end if
                    #end if

                    # Check to see if we need to retry the last query
                    if (tries == 0):
                        logger.debug('[--] Increment the counter variable')
                        currentFetchCount += rowsToFetch
                        logger.debug(f'[----] Current Fetch Count = {currentFetchCount}')
                    else:
                        logger.debug(f'[**] Pause for {sleepTimeSeconds} before retrying')
                        sleep(sleepTimeSeconds)
                    #end if

                    # Check to see if it is time to write out the buffer
                    if (currentFetchCount  > entriesPerFile * filenumber):
                        filename = f'{tableInfo["TableName"]}-{timestamp}-{filenumber:03}.json'
                        logger.info(f'[**] Open the file {filename} for the results')
                        with open(f'{outputDirectory}/{filename}', 'w', encoding="utf-8") as outputFile:
                            outputFile.write('[')
                            outputFile.write(outputString.getvalue())
                            outputFile.write(']')
                        #end with

                        # Increment the file number
                        filenumber += 1

                        # Close and re-initialize the string buffer
                        outputString.close()
                        outputString = StringIO()
                    #end if
                #end while

                logger.debug('[--] Write out the last file')
                filename = f'{tableInfo["TableName"]}-{timestamp}-{filenumber:03}.json'
                logger.info(f'[**] Open the file {filename} for the results')
                with open(f'{outputDirectory}/{filename}', 'w', encoding="utf-8") as outputFile:
                    outputFile.write('[')
                    outputFile.write(outputString.getvalue())
                    outputFile.write(']')
                #end with

                logger.debug('[--] Close the buffer')
                outputString.close()

                logger.debug(f'[--] Upload {filenumber} files')
                x = 1
                while x <= filenumber:
                    filename = f'{tableInfo["TableName"]}-{timestamp}-{x:03}.json'
                    destination = f'{tableInfo["TableName"]}/{filename}'

                    logger.info(f'[**] Upload the file {filename} to the Storage account')
                    logger.debug(f'[--] az storage blob upload --file {filename} --container-name logarchivecontainer --name "{destination}" --account-name csoclogarchive')
                    exitCode, results, logs = az(f'storage blob upload --file {outputDirectory}/{filename} --container-name logarchivecontainer --name "{destination}" --account-name csoclogarchive')

                    if exitCode == 0:
                        os.remove(f'{outputDirectory}/{filename}')
                    else:
                        logger.warning(f'[**] Problem uploading the file {filename}\n\t Exit code:{exitCode}\n\t Log Message: {logs}')

                    x += 1
                #end while
            #end for
        else:
            print(f'[!!] Error fetching table names and record counts\n Exit code:{exitCode}\nLog Message: {logs}')
        #end if
    
        logger.debug('[--] Increment the day')
        currentDay += timedelta(days=concurrentExports)
    #end while
except Exception as exc:
    logger.critical(exc)
logger.info('------------------------------ END ------------------------------')