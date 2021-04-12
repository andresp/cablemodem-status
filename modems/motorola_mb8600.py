from .observable_modem import ObservableModem
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import os
import pytz
import re
import requests
from influxdb_client import Point

class MotorolaMB8600(ObservableModem):
    baseUrl = ""
    hostname = ""
    session = None

    modemLogLevels = {
        3: logging.CRITICAL,
        5: logging.WARNING,
        6: logging.INFO
    }

    def __init__(self, config, dbClient, logger):
        self.hostname = config['Modem']['Host']
        self.baseUrl = "http://" + self.hostname
        self.session = requests.Session()

        super(MotorolaMB8600, self).__init__(config, dbClient, logger)

    def formatUpstreamPoints(self, data, sampleTime):
        points = []
        for index in range(1, len(data)):
            
            values = data[index].find_all("td")

            point = Point("upstreamQam") \
                .tag("channel", values[0].text) \
                .tag("lockStatus", values[1].text) \
                .tag("modulation", values[2].text) \
                .tag("channelId", int(values[3].text)) \
                .tag("symbolRate", int(values[4].text)) \
                .tag("frequency", values[5].text) \
                .time(sampleTime) \
                .field("power", float(values[6].text))

            points.append(point)

        return points

    def formatDownstreamPoints(self, data, sampleTime):
        points = []

        for index in range(1, len(data) - 1):

            values = data[index].find_all("td")
            measurement = ""
            if values[2].text == "OFDM PLC":
                measurement = "downstreamOFDM"
            else:
                measurement = "downstreamQam"
                
            point = Point(measurement) \
                .tag("channel", values[0].text) \
                .tag("lockStatus", values[1].text) \
                .tag("modulation", values[2].text) \
                .tag("channelId", values[3].text) \
                .tag("frequency", values[4].text) \
                .time(sampleTime) \
                .field("power", float(values[5].text)) \
                .field("snr", float(values[6].text)) \
                .field("correctables", int(values[7].text)) \
                .field("uncorrectables", int(values[8].text))

            points.append(point)

        return points

    def login(self):
        self.logger.info("Logging into modem")

        modemAuthentication = {
            'loginUsername': self.config['Modem']['Username'],
            'loginPassword': self.config['Modem']['Password']
        }
        loginUrl = "/goform/login"

        self.session.post(self.baseUrl + loginUrl, data=modemAuthentication)

    def collectStatus(self):
        self.logger.info("Getting modem status")

        sampleTime = datetime.utcnow().isoformat()
        response = self.session.get(self.baseUrl + "/MotoConnection.asp")

        # Extract status data
        statusPage = BeautifulSoup(response.content, features="lxml")
        tables = statusPage.find_all("table", { "class": "moto-table-content" })

        downstreamData = tables[3].find_all("tr")
        downstreamPoints = self.formatDownstreamPoints(downstreamData, sampleTime)

        upstreamData = tables[4].find_all("tr")
        upstreamPoints = self.formatUpstreamPoints(upstreamData, sampleTime)

        # Store data to InfluxDB
        self.write_api.write(bucket=self.influxBucket, record=downstreamPoints)
        self.write_api.write(bucket=self.influxBucket, record=upstreamPoints)

    def collectLogs(self):
        # Not implemented yet
        return