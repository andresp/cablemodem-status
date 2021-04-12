from .observable_modem import ObservableModem
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import os
import pytz
import re
import requests
from influxdb_client import Point

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
            
            point = Point("upstreamQam") \
                .tag("channel", data["channelIds"][index].text) \
                .tag("lockStatus", data["lockStatus"][index].text) \
                .tag("modulation", data["modulation"][index].text) \
                .tag("channelId", int(data["channelIds"][index].text)) \
                .tag("symbolRate", int(data["symbolRate"][index].text)) \
                .tag("usChannelType", data["channelType"][index].text) \
                .tag("frequency", data["frequency"][index].text.split()[0]) \
                .time(sampleTime) \
                .field("power", float(data["power"][index].text.split()[0]))

            points.append(point)

        return points

    def formatDownstreamPoints(self, data, sampleTime):
        points = []

        for index in range(len(data["channelIds"])):

            measurement = ""
            if data["modulation"][index].text == "OFDM":
                measurement = "downstreamOFDM"
            else:
                measurement = "downstreamQam"
                
            power = data["power"][index].text.split()[0]
            if power == "NA":
                power = "0"

            snr = data["snr"][index].text.split()[0]
            if snr == "NA":
                snr = 0

            point = Point(measurement) \
                .tag("channel", data["channelIds"][index].text) \
                .tag("lockStatus", data["lockStatus"][index].text) \
                .tag("modulation", data["modulation"][index].text) \
                .tag("channelId", int(data["channelIds"][index].text)) \
                .tag("frequency", data["frequencies"][index].text.split()[0]) \
                .time(sampleTime) \
                .field("power", float(power)) \
                .field("snr", float(snr)) \
                .field("subcarrierRange", "") \
                .field("uncorrected", int(data["uncorrected"][index].text)) \
                .field("correctables", int(data["corrected"][index].text)) \
                .field("uncorrectables", int(data["uncorrectable"][index].text))

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
        self.write_api.write(bucket=self.influxBucket, record=downstreamPoints)
        self.write_api.write(bucket=self.influxBucket, record=upstreamPoints)

    def collectLogs(self):
        # Not implemented yet        