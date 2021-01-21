from bs4 import BeautifulSoup
import configparser
from datetime import datetime
import functools
from influxdb import InfluxDBClient
import logging
import logging_loki
import os
import pytz
import re
import requests
from requests.packages import urllib3
import schedule
import time

def catch_exceptions(cancel_on_failure=False):
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                import traceback
                print(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator

class CustomTimestampFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'timestamp'):
            record.created = record.timestamp
        return True

def writeLastRuntime():
    if os.path.exists(lastRunFilename):
        os.utime(lastRunFilename, None)
    else:
        open(lastRunFilename, 'a').close()

def getLastRuntime():
    if os.path.exists(lastRunFilename):
        last = datetime.fromtimestamp(os.path.getmtime(lastRunFilename))
        return pytz.timezone(hostTimeZone).localize(last)
    else:
        return datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=pytz.utc)

def parseDelimitedTagValue(tagValue, noTrailingPipe = False):
    dataRowCountIndex = tagValue.index("|")
    dataRowsCount = int(tagValue[0:dataRowCountIndex])
    delimiterCount = tagValue.count("|")
    if noTrailingPipe:
        delimiterCount += 1
    dataRowFieldsCount = int((delimiterCount - 1) / dataRowsCount)
    dataRowFields = tagValue.split("|")
    dataRows = []
    for rowIndex in range(dataRowsCount):
        dataRows.append(dataRowFields[(rowIndex * dataRowFieldsCount) + 1: ((rowIndex + 1) * (dataRowFieldsCount) + 1)])

    return dataRows

def formatUpstreamQamPoints(data, sampleTime):
    points = []
    for row in data:
        point = {}
        point['measurement'] = "upstreamQam"
        point['tags'] = {}
        point['tags']['channel'] = row[0]
        point['tags']['lockStatus'] = row[1]
        point['tags']['usChannelType'] = row[2]
        point['tags']['channelId'] = int(row[3])
        point['tags']['symbolRate'] = int(row[4])
        point['tags']['frequency'] = row[5]
        point['time'] = sampleTime
        point['fields'] = {}
        point['fields']['power'] = float(row[6].split()[0])
        points.append(point)

    return points

def formatUpstreamOFDMAPoints(data, sampleTime):
    points = []
    for row in data:
        point = {}
        point['measurement'] = "upstreamOFDMA"
        point['tags'] = {}
        point['tags']['channel'] = row[0]
        point['tags']['lockStatus'] = row[1]
        point['tags']['modulation'] = row[2]
        point['tags']['channelId'] = int(row[3])
        point['tags']['frequency'] = row[4]
        point['time'] = sampleTime
        point['fields'] = {}
        point['fields']['power'] = float(row[5].split()[0])
        points.append(point)

    return points

def formatDownstreamQamPoints(data, sampleTime):
    points = []
    for row in data:
        point = {}
        point['measurement'] = "downstreamQam"
        point['tags'] = {}
        point['tags']['channel'] = row[0]
        point['tags']['lockStatus'] = row[1]
        point['tags']['modulation'] = row[2]
        point['tags']['channelId'] = int(row[3])
        point['tags']['frequency'] = row[4]
        point['time'] = sampleTime
        point['fields'] = {}
        point['fields']['power'] = float(row[5].split()[0])
        point['fields']['snr'] = float(row[6].split()[0])
        point['fields']['correctables'] = int(row[7])
        point['fields']['uncorrectables'] = int(row[8])
        points.append(point)

    return points

def formatDownstreamOFDMPoints(data, sampleTime):
    points = []
    for row in data:
        point = {}
        point['measurement'] = "downstreamOFDM"
        point['tags'] = {}
        point['tags']['channel'] = row[0]
        point['tags']['lockStatus'] = row[1]
        point['tags']['modulation'] = row[2]
        point['tags']['channelId'] = int(row[3])
        point['tags']['frequency'] = row[4]
        point['time'] = sampleTime
        point['fields'] = {}
        point['fields']['power'] = float(row[5].split()[0])
        point['fields']['snr'] = float(row[6].split()[0])
        point['fields']['subcarrierRange'] = row[7]
        point['fields']['uncorrected'] = int(row[8])
        point['fields']['correctables'] = int(row[9])
        point['fields']['uncorrectables'] = int(row[10])
        points.append(point)

    return points

@catch_exceptions(cancel_on_failure=False)
def collectionJob():

    consoleLogger.info("Logging into modem")

    session = requests.Session()
    response = session.get(baseUrl, verify=False)

    # Get login url
    loginPage = BeautifulSoup(response.content, features="lxml")

    loginForm = loginPage.select("#target")
    loginUrl = loginForm[0].get("action")

    # Login
    response = session.post(baseUrl + loginUrl, data=modemAuthentication, verify=False)

    # Get status
    consoleLogger.info("Getting modem status")

    sampleTime = datetime.utcnow().isoformat()
    response = session.get(baseUrl + "/DocsisStatus.htm", verify=False)

    # Extract status data
    statusPage = BeautifulSoup(response.content, features="lxml")
    script = statusPage.select("head > script:nth-child(24)")
    scriptText = str(script[0].contents[0])

    matches = re.findall("(var tagValueList = \'([^\']+)\';)", scriptText, re.MULTILINE)
    if matches:
        upstreamQamValues = matches[1][1]
        downstreamQamValues = matches[2][1]
        upstreamOFDMAValues = matches[3][1]
        downstreamOFDMValues = matches[4][1]

        upstreamQamChannels = parseDelimitedTagValue(upstreamQamValues)
        downstreamQamChannels = parseDelimitedTagValue(downstreamQamValues)
        upstreamOFDMAChannels = parseDelimitedTagValue(upstreamOFDMAValues, noTrailingPipe=True)
        downstreamOFDMChannels = parseDelimitedTagValue(downstreamOFDMValues)

        upstreamQamPoints = formatUpstreamQamPoints(upstreamQamChannels, sampleTime)
        downstreamQamPoints = formatDownstreamQamPoints(downstreamQamChannels, sampleTime)
        upstreamOFDMAPoints = formatUpstreamOFDMAPoints(upstreamOFDMAChannels, sampleTime)
        downstreamOFDMPoints = formatDownstreamOFDMPoints(downstreamOFDMChannels, sampleTime)

        # Store data to InfluxDB
        # dbClient.write_points(upstreamQamPoints)
        # dbClient.write_points(downstreamQamPoints)
        # dbClient.write_points(upstreamOFDMAPoints)
        # dbClient.write_points(downstreamOFDMPoints)

    if collectLogs:

        consoleLogger.info("Getting event logs")

        lastRunTime = getLastRuntime()

        handler = logging_loki.LokiHandler(
            url=lokiUrl + "/loki/api/v1/push", 
            tags={'application': "cablemodem-status-logs"},
            auth=(lokiUsername, lokiPassword),
            version="1",
        )

        filter = CustomTimestampFilter()

        logger = logging.getLogger("modem")
        logger.addHandler(handler)
        logger.addFilter(filter)
            
        eventLogResponse = session.get(baseUrl + "/eventLog.htm", verify=False)

        # Extract status data
        eventLogPage = BeautifulSoup(eventLogResponse.content, features="lxml")
        eventLogScript = eventLogPage.select("head > script:nth-child(23)")
        scriptText = str(eventLogScript[0].contents[0])

        matches = re.findall("(var xmlFormat = \"([^\"]+)\";)", scriptText, re.MULTILINE)
        if matches:
            logEntriesXml = matches[0][1].replace('\\/', '/')
            logs = BeautifulSoup(logEntriesXml, features="lxml")
            
            for entry in logs.find_all('tr'):
                timestampValue = entry.docsdevevtime.text

                if timestampValue == "Time Not Established":
                    timestampValue = datetime.now(tz=pytz.timezone(logTimeZone)).strftime('%a %b %d %H:%M:%S %Y')

                logTimestamp = datetime.strptime(timestampValue, '%a %b %d %H:%M:%S %Y')
                logTimestamp = pytz.timezone(logTimeZone).localize(logTimestamp)
                if logTimestamp > lastRunTime:
                    message = entry.docsdevevtext.text

                    eventTypeCode = None
                    eventTypeCodeSearch = re.search(r'Event Type Code: ([\d]+)', message)
                    if eventTypeCodeSearch:
                        eventTypeCode = eventTypeCodeSearch.group(1)

                    eventChannelId = None
                    eventChannelIdSearch = re.search(r'Chan ID: ([\d]+)', message)
                    if eventChannelIdSearch:
                        eventChannelId = eventChannelIdSearch.group(1)

                    logLevel = int(re.search(r'([\d]+)', entry.docsdevevlevel.text).group(1))

                    logger.log(modemLogLevels[logLevel], message, extra={'timestamp': logTimestamp.timestamp(), 'tags': {
                        'logLevel': entry.docsdevevlevel.text, 
                        'hostname': modemHostname,
                        'eventTypeCode': eventTypeCode,
                        'eventChannelId': eventChannelId}})

        writeLastRuntime()

    consoleLogger.info("Done collecting status and logs")

# Init logger
logging.basicConfig(level=logging.INFO)
consoleLogger = logging.getLogger("app")

# Read configuration
consoleLogger.info("Reading configuration")

config = configparser.ConfigParser()
config.read('data/configuration.ini')

influxDatabase = config['Database']['Name']
influxHost = config['Database']['Host']
influxPort = int(config['Database']['Port'])
influxUser = config['Database']['Username']
influxPassword = config['Database']['Password']

collectLogs = config['Modem'].getboolean('CollectLogs')
logTimeZone = config['Modem']['LogTimezone']
hostTimeZone = config['General']['HostTimezone']

lokiUrl = config['Loki']['Url']
lokiUsername = config['Loki']['Username']
lokiPassword = config['Loki']['Password']

runAsDaemon = config['General'].getboolean('Daemon')
runEveryMinutes = int(config['General']['RunEveryMinutes'])

modemAuthentication = {
    'loginName': "admin",
    'loginPassword': config['Modem']['Password']
}

modemLogLevels = {
    3: logging.CRITICAL,
    5: logging.WARNING,
    6: logging.INFO
}

consoleLogger.info("Connecting to InfluxDB")

dbClient = InfluxDBClient(host=influxHost, port=influxPort, username=influxUser, password=influxPassword)
dbClient.switch_database(influxDatabase)
modemHostname = config['Modem']['Host']
baseUrl = "https://" + modemHostname

lastRunFilename = "data/cablemodem-status.last"

# Because the modem uses a self-signed certificate and this is expected, disabling the warning to reduce noise.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if runAsDaemon:
    collectionJob()
    consoleLogger.info("Running as daemon")
    schedule.every(runEveryMinutes).minutes.do(collectionJob)

    while 1:
        schedule.run_pending()
        time.sleep(1)
else:
    consoleLogger.info("One-time execution")
    collectionJob()