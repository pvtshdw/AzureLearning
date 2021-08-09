import argparse # Used to parse command-line arguments
import pandas  # Used to read Excel files and output JSON
import os # Used to get just the base file name without the extension

print('----- Conversion starting -----')

# Set the command-line arguments
parser = argparse.ArgumentParser(description="This script reads a tab from an excel file and converts it to JSON format.")
parser.add_argument("-i", "--inputfile", type=str, help="The path and name of the Excel file to parse")
parser.add_argument("-t", "--tabname", type=str, default="Indicators", help="The name of the tab to read (Default=Indicators")

# Parse the command-line arguments
args = parser.parse_args()

# Set the output file name to be the same as the input file, but with a .json extension
outputfile = os.path.splitext(args.inputfile)[0] + ".json"

# Read the excel file
excel_data_df = pandas.read_excel(args.inputfile, sheet_name=args.tabname)

# Output the JSON string
json_str = excel_data_df.to_json(orient='records')

# Open the output file
with open(outputfile, 'w') as f:
    f.write(json_str)

print('----- Conversion complete! -----')