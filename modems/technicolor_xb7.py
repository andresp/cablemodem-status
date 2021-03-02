from .observable_modem import ObservableModem
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import os
import pytz
import re
import requests

class TechnicolorXB7(ObservableModem):
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
        self.baseUrl = "http://" + self.hostname
        self.session = requests.Session()

        super(TechnicolorXB7, self).__init__(config, dbClient, logger)

    def formatUpstreamPoints(self, data, sampleTime):
        points = []
        for index in range(len(data["channelIds"])):
            
            point = {}
            point['measurement'] = "upstreamQam"
            point['tags'] = {}
            point['tags']['channel'] = data["channelIds"][index].text
            point['tags']['lockStatus'] = data["lockStatus"][index].text
            point['tags']['modulation'] = data["modulation"][index].text
            point['tags']['channelId'] = int(data["channelIds"][index].text)
            point['tags']['symbolRate'] = int(data["symbolRate"][index].text)
            point['tags']['usChannelType'] = data["channelType"][index].text
            point['tags']['frequency'] = data["frequency"][index].text.split()[0]
            point['time'] = sampleTime
            point['fields'] = {}
            point['fields']['power'] = float(data["power"][index].text.split()[0])
            points.append(point)

        return points

    def formatDownstreamPoints(self, data, sampleTime):
        points = []

        for index in range(len(data["channelIds"])):
            point = {}

            measurement = ""
            if data["modulation"][index].text == "OFDM":
                measurement = "downstreamOFDM"
            else:
                measurement = "downstreamQam"

            point['measurement'] = measurement
            point['tags'] = {}
            point['tags']['channel'] = data["channelIds"][index].text
            point['tags']['lockStatus'] = data["lockStatus"][index].text
            point['tags']['modulation'] = data["modulation"][index].text
            point['tags']['channelId'] = int(data["channelIds"][index].text)
            point['tags']['frequency'] = data["frequencies"][index].text.split()[0]
            point['time'] = sampleTime
            point['fields'] = {}
            power = data["power"][index].text.split()[0]
            if power == "NA":
                power = "0"

            point['fields']['power'] = float(power)

            snr = data["snr"][index].text.split()[0]
            if snr == "NA":
                snr = 0

            point['fields']['snr'] = float(snr)
            point['fields']['subcarrierRange'] = ""
            point['fields']['uncorrected'] = int(data["uncorrected"][index].text)
            point['fields']['correctables'] = int(data["corrected"][index].text)
            point['fields']['uncorrectables'] = int(data["uncorrectable"][index].text)
            points.append(point)

        return points

    def login(self):
        self.logger.info("Logging into modem")

        modemAuthentication = {
            'username': self.config['Modem']['Username'],
            'password': self.config['Modem']['Password']
        }
        loginUrl = "/check.php"

        self.session.post(self.baseUrl + loginUrl, data=modemAuthentication)

    def collectStatus(self):
        self.logger.info("Getting modem status")

        sampleTime = datetime.utcnow().isoformat()
        response = self.session.get(self.baseUrl + "/network_setup.php")

        # Extract status data
        statusPage = BeautifulSoup(response.content, features="lxml")

        tables = statusPage.find_all("table", { "class": "data" })
        downstreamData = tables[0].select("tbody > tr")
        codewordsData = tables[2].select("tbody > tr")

        downstream = {
            "channelIds": downstreamData[0].select("td > div"),
            "lockStatus": downstreamData[1].select("td > div"),
            "frequencies": downstreamData[2].select("td > div"),
            "snr": downstreamData[3].select("td > div"),
            "power": downstreamData[4].select("td > div"),
            "modulation": downstreamData[5].select("td > div"),
            "uncorrected": codewordsData[0].select("td > div"),
            "corrected": codewordsData[1].select("td > div"),
            "uncorrectable": codewordsData[2].select("td > div")
        }

        downstreamPoints = self.formatDownstreamPoints(downstream, sampleTime)

        upstreamData = tables[1].select("tbody > tr")
        upstream = {
            "channelIds": upstreamData[0].select("td > div"),
            "lockStatus": upstreamData[1].select("td > div"),
            "frequency": upstreamData[2].select("td > div"),
            "symbolRate": upstreamData[3].select("td > div"),
            "power": upstreamData[4].select("td > div"),
            "modulation": upstreamData[5].select("td > div"),
            "channelType": upstreamData[6].select("td > div")
        }

        upstreamPoints = self.formatUpstreamPoints(upstream, sampleTime)

        # Store data to InfluxDB
        self.dbClient.write_points(downstreamPoints)
        self.dbClient.write_points(upstreamPoints)

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
        # eventLogResponse = self.session.get(self.baseUrl + "/eventLog.htm", verify=False)

        # # Extract status data
        # eventLogPage = BeautifulSoup(eventLogResponse.content, features="lxml")
        # eventLogScript = eventLogPage.select("head > script:nth-child(23)")
        # scriptText = str(eventLogScript[0].contents[0])

        # matches = re.findall("(var xmlFormat = \"([^\"]+)\";)", scriptText, re.MULTILINE)
        # if matches:
        #     logEntriesXml = matches[0][1].replace('\\/', '/')
        #     logs = BeautifulSoup(logEntriesXml, features="lxml")
            
        #     entries = logs.find_all('tr')
        #     for index, entry in enumerate(entries):
        #         timestampValue = entry.docsdevevtime.text

        #         if timestampValue == "Time Not Established":
        #             # Find next entry with a valid timestamp, if any

        #             foundTimestamp = False
        #             if len(entries) > index + 1:
        #                 for nextEntry in entries[index + 1 : ]:
        #                     nextEntryTimestamp = nextEntry.docsdevevtime.text
        #                     if nextEntryTimestamp != "Time Not Established":
        #                         timestampValue = nextEntryTimestamp
        #                         foundTimestamp = True
        #                         break

        #             if foundTimestamp == False:
        #                 # Use sampleTime for unknown timestamp
        #                 timestampValue = sampleTime.strftime('%a %b %d %H:%M:%S %Y')

        #         logTimestamp = datetime.strptime(timestampValue, '%a %b %d %H:%M:%S %Y')
        #         logTimestamp = pytz.timezone(self.logTimeZone).localize(logTimestamp)
        #         if logTimestamp > lastRunTime:
        #             message = entry.docsdevevtext.text

        #             eventTypeCode = None
        #             eventTypeCodeSearch = re.search(r'Event Type Code: ([\d]+)', message)
        #             if eventTypeCodeSearch:
        #                 eventTypeCode = eventTypeCodeSearch.group(1)

        #             eventChannelId = None
        #             eventChannelIdSearch = re.search(r'Chan ID: ([\d]+)', message)
        #             if eventChannelIdSearch:
        #                 eventChannelId = eventChannelIdSearch.group(1)

        #             logLevel = int(re.search(r'([\d]+)', entry.docsdevevlevel.text).group(1))

        #             self.logger.log(self.modemLogLevels[logLevel], message, extra={'timestamp': logTimestamp.timestamp(), 'tags': {
        #                 'logLevel': entry.docsdevevlevel.text, 
        #                 'hostname': self.hostname,
        #                 'eventTypeCode': eventTypeCode,
        #                 'eventChannelId': eventChannelId}})

        self.writeLastRuntime()
