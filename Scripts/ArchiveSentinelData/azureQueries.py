# -----------------------------------------------------------------------------
# Queries for all other tables
# -----------------------------------------------------------------------------
getTableRowCountsByHour = """union withsource=TableName AuditLogs
//    , AWSCloudTrail
//    , AzureActivity // Need to encode embedded JSON
//    , BehaviorAnalytics
//    , cisco_umbrella_CL
//    , DeviceEvents
//    , DeviceFileEvents
//    , DeviceInfo
//    , DeviceLogonEvents
//    , DeviceNetworkEvents
//    , DeviceNetworkInfo
//    , DeviceProcessEvents
//    , DeviceRegistryEvents
//    , DnsEvents
//    , DnsInventory
//    , Event
//    , InformationProtectionLogs_CL
//    , OfficeActivity // CRITICAL - 'charmap' codec can't encode character '\u2010' in position 22538596: character maps to <undefined>
//    , ProtectionStatus
//    , SecurityAlert
//    , SecurityDetection
//    , SecurityEvent
//    , SecurityIncident
//    , SigninLogs
//    , UserAccessAnalytics
//    , UserPeerAnalytics
| where TimeGenerated between (startofday(todatetime('STARTDATE')) .. endofday(todatetime('STARTDATE')))
//| where TimeGenerated between (todatetime('4/7/2021, 12:00:00.000 AM') .. todatetime('4/7/2021, 11:59:59.999 PM'))
| summarize RowCount = count(), Size = sum(_BilledSize) by bin(TimeGenerated, 1h), TableName
| project TimeGenerated
    , TableName
    , RowCount
    , SizePerEntry = bin(Size/RowCount, 10)
//    , EntriesPerCall = bin(64000000 / (Size / RowCount), 1000)
| order by TimeGenerated asc, TableName asc"""

getTableData = """TABLENAME
| where TimeGenerated between (todatetime('STARTTIME') .. datetime_add('hour', 1, todatetime('STARTTIME')))
| serialize RowNumber = row_number(1)
| where RowNumber between (STARTINDEX .. ENDINDEX)"""

# -----------------------------------------------------------------------------
# Queries for Syslog only
# -----------------------------------------------------------------------------
getFilteredSyslogRowCount = """let ComputerList = dynamic([
'10.0.0.1', '10.0.0.2', 'some hostname'
]);
Syslog
| where TimeGenerated between (startofday(todatetime('STARTDATE')) .. endofday(todatetime('STARTDATE')))
//| where TimeGenerated between (todatetime('4/7/2021, 12:00:00.000 AM') .. todatetime('4/7/2021, 11:59:59.999 PM'))
| where Computer in (ComputerList)
| summarize RowCount = count(), Size = sum(_BilledSize) by bin(TimeGenerated, 1h)
| project TimeGenerated
    , TableName = 'Syslog'
    , RowCount
    , SizePerEntry = bin(Size/RowCount, 10)
    , EntriesPerCall = bin(64000000 / (Size / RowCount), 1000)
| order by TimeGenerated asc"""

getSyslogData = """let ComputerList = dynamic([
'10.0.0.1', '10.0.0.2', 'some hostname'
]);
TABLENAME
| where TimeGenerated between 
    (todatetime('STARTTIME') .. datetime_add('hour', 1, todatetime('STARTTIME')))
| where Computer in (ComputerList)
| serialize RowNumber = row_number(1)
| where RowNumber between (STARTINDEX .. ENDINDEX)"""

# -----------------------------------------------------------------------------
# Queries for SecurityEvent
# -----------------------------------------------------------------------------
getSecurityEventRowCountsByHour = """SecurityEvent
| where TimeGenerated between (startofday(todatetime('STARTDATE')) .. endofday(todatetime('STARTDATE')))
| where EventID !in (5058, 5061)  // RISK 7451
//| where TimeGenerated between (todatetime('4/7/2021, 12:00:00.000 AM') .. todatetime('4/7/2021, 11:59:59.999 PM'))
| summarize RowCount = count(), Size = sum(_BilledSize) by bin(TimeGenerated, 1h)
| project TimeGenerated
    , TableName = 'SecurityEvent'
    , RowCount
    , SizePerEntry = bin(Size/RowCount, 10)
//    , EntriesPerCall = bin(64000000 / (Size / RowCount), 1000)
| order by TimeGenerated asc"""

getSecurityEventData = """TABLENAME
| where TimeGenerated between (todatetime('STARTTIME') .. datetime_add('hour', 1, todatetime('STARTTIME')))
| where EventID !in (5058, 5061)  // RISK 7451
// Only output columns that have data
| project TimeGenerated
    , SourceSystem
    , Account
    , AccountType
    , Computer
    , EventSourceName
    , Channel
    , Task
    , Level
    , EventData
    , EventID
    , Activity
    , AccessList
    , AccessMask
    , AccessReason
    , AccountDomain
    , AccountName
    , AdditionalInfo
    , AdditionalInfo2
    , AuthenticationPackageName
    , CallerProcessId
    , CallerProcessName
    , ClassId
    , ClassName
    , ClientAddress
    , ClientName
    , CommandLine
    , CompatibleIds
    , DeviceDescription
    , DeviceId
    , ElevatedToken
    , FailureReason
    , FileHash
    , FilePath
    , FilePathNoUser
    , Fqbn
    , HandleId
    , ImpersonationLevel
    , IpAddress
    , IpPort
    , KeyLength
    , LmPackageName
    , LocationInformation
    , LogonGuid
    , LogonID
    , LogonProcessName
    , LogonType
    , LogonTypeName
    , MandatoryLabel
    , MemberName
    , MemberSid
    , NewProcessId
    , NewProcessName
    , ObjectName
    , ObjectServer
    , ObjectType
    , OperationType
    , ParentProcessName
    , PrivilegeList
    , Process
    , ProcessId
    , ProcessName
    , Properties
    , RelativeTargetName
    , RestrictedAdminMode
    , SamAccountName
    , ServiceAccount
    , ServiceFileName
    , ServiceName
    , ServiceStartType
    , ServiceType
    , SessionName
    , ShareLocalPath
    , ShareName
    , SidHistory
    , Status
    , SubjectAccount
    , SubjectDomainName
    , SubjectLogonId
    , SubjectUserName
    , SubjectUserSid
    , SubStatus
    , TargetAccount
    , TargetDomainName
    , TargetInfo
    , TargetLinkedLogonId
    , TargetLogonGuid
    , TargetLogonId
    , TargetOutboundDomainName
    , TargetOutboundUserName
    , TargetServerName
    , TargetSid
    , TargetUser
    , TargetUserName
    , TargetUserSid
    , TokenElevationType
    , TransmittedServices
    , VirtualAccount
    , VendorIds
    , Workstation
    , WorkstationName
    , SourceComputerId
    , EventOriginId
    , MG
    , TimeCollected
    , ManagementGroupName
    , Type
    , _ResourceId
| serialize RowNumber = row_number(1)
| where RowNumber between (STARTINDEX .. ENDINDEX)"""

