from bs4 import BeautifulSoup
from datetime import datetime
from influxdb_client import Point
import requests

from .observablemodem import ObservableModem

class HitronCoda56(ObservableModem):
    baseUrl = ""
    hostname = ""
    session = None

    def __init__(self, config, logger):
        self.hostname = config['Modem']['Host']
        self.baseUrl = "http://" + self.hostname
        self.session = requests.Session()

        super(HitronCoda56, self).__init__(config, logger)

    def formatUpstreamPoints(self, data, sampleTime):
        points = []
        for index in range(1, len(data)):
            
            values = data[index].find_all("td")

            point = Point("upstreamQam") \
                .tag("channel", values[0].text) \
                .tag("modulation", values[3].text) \
                .tag("mode", values[4].text) \
                .tag("channelId", int(values[6].text)) \
                .tag("symbolRate", int(values[2].text)) \
                .tag("frequency", values[1].text) \
                .time(sampleTime) \
                .field("power", float(values[5].text))

            points.append(point)

        return points

    def formatUpstreamOfdmaPoints(self, data, sampleTime):
        points = []
        for index in range(1, len(data)):
            
            values = data[index].find_all("td")

            if values[1].text == "DISABLED":
                continue

            point = Point("upstreamOfdma") \
                .tag("channel", values[0].text) \
                .tag("modulation", "OFDMA") \
                .tag("channelId", int(values[0].text)) \
                .tag("frequency", values[2].text) \
                .tag("fftsize", values[8].text) \
                .time(sampleTime) \
                .field("lindigitalatt", float(values[3].text)) \
                .field("digitalatt", float(values[4].text)) \
                .field("bw", float(values[5].text)) \
                .field("power", float(values[6].text)) \
                .field("power1_6", float(values[7].text)) \

            points.append(point)

        return points

    def formatDownstreamPoints(self, data, sampleTime):
        points = []

        for index in range(1, len(data) - 1):

            values = data[index].find_all("td")
            measurement = ""
              
            point = Point(measurement) \
                .tag("channel", values[0].text) \
                .tag("modulation", values[2].text) \
                .tag("channelId", values[8].text) \
                .tag("frequency", values[1].text) \
                .time(sampleTime) \
                .field("power", float(values[3].text)) \
                .field("snr", float(values[4].text)) \
                .field("octetts", int(values[5].text)) \
                .field("correctables", int(values[6].text)) \
                .field("uncorrectables", int(values[7].text))

            points.append(point)

        return points

    def formatDownstreamOfdmPoints(self, data, sampleTime):
        points = []

        for index in range(1, len(data) - 1):

            values = data[index].find_all("td")
            measurement = ""
            
            if values[3] != "YES":
                continue

            point = Point(measurement) \
                .tag("receiver", values[0].text) \
                .tag("modulation", "OFDM") \
                .tag("ffttype", values[1].text) \
                .tag("frequency", values[2].text) \
                .time(sampleTime) \
                .field("power", float(values[6].text)) \
                .field("snr", float(values[7].text)) \
                .field("octetts", int(values[8].text)) \
                .field("correctables", int(values[9].text)) \
                .field("uncorrectables", int(values[10].text))

            points.append(point)

        return points

    def login(self):
        pass

    def collectStatus(self):
        self.logger.info("Getting modem status")

        sampleTime = datetime.utcnow().isoformat()
        response = self.session.get(self.baseUrl + "/index.html#status_docsis/m/1/s/2")

        # Extract status data
        statusPage = BeautifulSoup(response.content, features="lxml")
        downstreamTable = statusPage.find(id="dsInfo")

        downstreamData = downstreamTable[3].find_all("tr")
        downstreamPoints = self.formatDownstreamPoints(downstreamData, sampleTime)

        downstreamTableOfdm = statusPage.find(id="dsofdmInfo")
        downstreamOfdmPoints = self.formatDownstreamOfdmPoints(downstreamTableOfdm, sampleTime)

        upstreamData = statusPage.find(id="usInfo")
        upstreamPoints = self.formatUpstreamPoints(upstreamData, sampleTime)

        upstreamOfdmaData = statusPage.find(id="usofdmInfo")
        upstreamOfdmaPoints = self.formatUpstreamOfdmaPoints(upstreamOfdmaData, sampleTime)

        # Store data to InfluxDB
        self.timeseriesWriter.write(record=downstreamPoints)
        self.timeseriesWriter.write(record=downstreamOfdmPoints)
        self.timeseriesWriter.write(record=upstreamPoints)
        self.timeseriesWriter.write(record=upstreamOfdmaPoints)

    def collectLogs(self):
        # Not implemented yet
        pass