from .observable_modem import ObservableModem
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import os
import pytz
import re
import requests

class NetgearCM2000(ObservableModem):
    baseUrl = ""
    hostname = ""
    session = None

    modemLogLevels = {
        3: logging.CRITICAL,
        5: logging.WARNING,
        6: logging.INFO
    }

    lastRunFilename = "data/cablemodem-status.last"

    def __init__(self, config, dbClient, logger):
        self.hostname = config['Modem']['Host']
        self.baseUrl = "https://" + self.hostname
        self.session = requests.Session()

        super(NetgearCM2000, self).__init__(config, dbClient, logger)

    def parseDelimitedTagValue(self, tagValue, noTrailingPipe = False):
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

    def formatUpstreamQamPoints(self, data, sampleTime):
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

    def formatUpstreamOFDMAPoints(self, data, sampleTime):
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

    def formatDownstreamQamPoints(self, data, sampleTime):
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

    def formatDownstreamOFDMPoints(self, data, sampleTime):
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

    def login(self):
        self.logger.info("Logging into modem")

        modemAuthentication = {
            'loginName': "admin",
            'loginPassword': self.config['Modem']['Password']
        }

        response = self.session.get(self.baseUrl, verify=False)

        # Get login url
        loginPage = BeautifulSoup(response.content, features="lxml")

        loginForm = loginPage.select("#target")
        loginUrl = loginForm[0].get("action")

        response = self.session.post(self.baseUrl + loginUrl, data=modemAuthentication, verify=False)

    def collectStatus(self):
        self.logger.info("Getting modem status")

        sampleTime = datetime.utcnow().isoformat()
        response = self.session.get(self.baseUrl + "/DocsisStatus.htm", verify=False)

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

            upstreamQamChannels = self.parseDelimitedTagValue(upstreamQamValues)
            downstreamQamChannels = self.parseDelimitedTagValue(downstreamQamValues)
            upstreamOFDMAChannels = self.parseDelimitedTagValue(upstreamOFDMAValues, noTrailingPipe=True)
            downstreamOFDMChannels = self.parseDelimitedTagValue(downstreamOFDMValues)

            upstreamQamPoints = self.formatUpstreamQamPoints(upstreamQamChannels, sampleTime)
            downstreamQamPoints = self.formatDownstreamQamPoints(downstreamQamChannels, sampleTime)
            upstreamOFDMAPoints = self.formatUpstreamOFDMAPoints(upstreamOFDMAChannels, sampleTime)
            downstreamOFDMPoints = self.formatDownstreamOFDMPoints(downstreamOFDMChannels, sampleTime)

            # Store data to InfluxDB
            self.dbClient.write_points(upstreamQamPoints)
            self.dbClient.write_points(downstreamQamPoints)
            self.dbClient.write_points(upstreamOFDMAPoints)
            self.dbClient.write_points(downstreamOFDMPoints)

    def writeLastRuntime(self):
        if os.path.exists(self.lastRunFilename):
            os.utime(self.lastRunFilename, None)
        else:
            open(self.lastRunFilename, 'a').close()

    def getLastRuntime(self):
        if os.path.exists(self.lastRunFilename):
            lastTimestamp = datetime.utcfromtimestamp(os.path.getmtime(self.lastRunFilename))
            return pytz.timezone("UTC").localize(lastTimestamp)
        else:
            return datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=pytz.utc)

    def collectLogs(self):
        self.logger.info("Getting modem event logs")

        sampleTime = datetime.utcnow().isoformat()

        lastRunTime = self.getLastRuntime()
        eventLogResponse = self.session.get(self.baseUrl + "/eventLog.htm", verify=False)

        # Extract status data
        eventLogPage = BeautifulSoup(eventLogResponse.content, features="lxml")
        eventLogScript = eventLogPage.select("head > script:nth-child(23)")
        scriptText = str(eventLogScript[0].contents[0])

        matches = re.findall("(var xmlFormat = \"([^\"]+)\";)", scriptText, re.MULTILINE)
        if matches:
            logEntriesXml = matches[0][1].replace('\\/', '/')
            logs = BeautifulSoup(logEntriesXml, features="lxml")
            
            entries = logs.find_all('tr')
            for index, entry in enumerate(entries):
                timestampValue = entry.docsdevevtime.text

                if timestampValue == "Time Not Established":
                    # Find next entry with a valid timestamp, if any

                    foundTimestamp = False
                    if len(entries) > index + 1:
                        for nextEntry in entries[index + 1 : ]:
                            nextEntryTimestamp = nextEntry.docsdevevtime.text
                            if nextEntryTimestamp != "Time Not Established":
                                timestampValue = nextEntryTimestamp
                                foundTimestamp = True
                                break

                    if foundTimestamp == False:
                        # Use sampleTime for unknown timestamp
                        timestampValue = sampleTime.strftime('%a %b %d %H:%M:%S %Y')

                logTimestamp = datetime.strptime(timestampValue, '%a %b %d %H:%M:%S %Y')
                logTimestamp = pytz.timezone(self.logTimeZone).localize(logTimestamp)
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

                    self.logger.log(self.modemLogLevels[logLevel], message, extra={'timestamp': logTimestamp.timestamp(), 'tags': {
                        'logLevel': entry.docsdevevlevel.text, 
                        'hostname': self.hostname,
                        'eventTypeCode': eventTypeCode,
                        'eventChannelId': eventChannelId}})

        self.writeLastRuntime()
