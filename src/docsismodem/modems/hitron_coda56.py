import json
from datetime import datetime, timezone
from influxdb_client import Point
import requests

from .observablemodem import ObservableModem

class HitronCoda56(ObservableModem):
    baseUrl = ""
    hostname = ""
    session = None

    def __init__(self, config, logger):
        self.hostname = config['Modem']['Host']
        self.baseUrl = "https://" + self.hostname
        self.session = requests.Session()

        super(HitronCoda56, self).__init__(config, logger)

    def formatUpstreamPoints(self, data, sampleTime):
        points = []
        for index in range(0, len(data)):
            
            values = data[index]

            point = Point("upstreamQam") \
                .tag("channel", values["portId"]) \
                .tag("modulation",  values["modtype"]) \
                .tag("mode", values["scdmaMode"]) \
                .tag("symbolRate", int(values["bandwidth"])) \
                .tag("channelId", int(values["channelId"])) \
                .tag("frequency", values["frequency"]) \
                .time(sampleTime) \
                .field("power", float(values["signalStrength"]))

            points.append(point)

        return points

    def formatUpstreamOfdmaPoints(self, data, sampleTime):
        points = []
        for index in range(0, len(data)):
            
            values = data[index]

            if values["state"] == '  DISABLED':
                continue

            point = Point("upstreamOfdma") \
                .tag("channel", values["uschindex"]) \
                .tag("modulation", "OFDMA") \
                .tag("channelId", int(values["uschindex"])) \
                .tag("frequency", values["frequency"]) \
                .tag("fftsize", values["fftVal"]) \
                .time(sampleTime) \
                .field("digatten", float(values["digAtten"])) \
                .field("digattenbo", float(values["digAttenBo"])) \
                .field("channelbw", float(values["channelBw"])) \
                .field("reppower", float(values["repPower"])) \
                .field("reppower1_6", float(values["repPower1_6"]))

            points.append(point)

        return points

    def formatDownstreamPoints(self, data, sampleTime):
        points = []

        for index in range(0, len(data)):

            values = data[index]
              
            point = Point("downstreamQam") \
                .tag("channel", values["portId"]) \
                .tag("modulation",  "256QAM" if values["modulation"] == "2" else '"') \
                .tag("channelId", int(values["channelId"])) \
                .tag("frequency", values["frequency"]) \
                .time(sampleTime) \
                .field("power", float(values["signalStrength"])) \
                .field("snr", float(values["snr"])) \
                .field("octets", int(values["dsoctets"])) \
                .field("correctables", int(values["correcteds"])) \
                .field("uncorrectables", int(values["uncorrect"]))

            points.append(point)

        return points

    def formatDownstreamOfdmPoints(self, data, sampleTime):
        points = []

        for index in range(0, len(data)):

            values = data[index]
            
            if values["plclock"] != 'YES':
                continue

            point = Point("downstreamOFDM") \
                .tag("receiver", values["receive"]) \
                .tag("modulation", "OFDM") \
                .tag("ffttype", values["ffttype"]) \
                .tag("frequency", values["Subcarr0freqFreq"]) \
                .time(sampleTime) \
                .field("power", float(values["plcpower"])) \
                .field("snr", float(values["SNR"])) \
                .field("octets", int(values["dsoctets"])) \
                .field("correctables", int(values["correcteds"])) \
                .field("uncorrectables", int(values["uncorrect"]))

            points.append(point)

        return points

    def login(self):
        pass

    def collectStatus(self):
        self.logger.info("Getting modem status")

        sampleTime = datetime.now(timezone.utc).isoformat()
        now = datetime.now(timezone.utc).timestamp

        # QAM down
        response = self.session.get(self.baseUrl + "/data/dsinfo.asp?_=" + str(now), verify=False)
        downstreamData = json.loads(response.text)
        downstreamPoints = self.formatDownstreamPoints(downstreamData, sampleTime)

        # OFDM down
        response = self.session.get(self.baseUrl + "/data/dsofdminfo.asp?_=" + str(now), verify=False)
        downstreamTableOfdm = json.loads(response.text)
        downstreamOfdmPoints = self.formatDownstreamOfdmPoints(downstreamTableOfdm, sampleTime)

        # TDMA up
        response = self.session.get(self.baseUrl + "/data/usinfo.asp?_=" + str(now), verify=False)
        upstreamData = json.loads(response.text)
        upstreamPoints = self.formatUpstreamPoints(upstreamData, sampleTime)

        # OFDMA up
        response = self.session.get(self.baseUrl + "/data/usofdminfo.asp?_=" + str(now), verify=False)
        upstreamOfdmaData = json.loads(response.text)
        upstreamOfdmaPoints = self.formatUpstreamOfdmaPoints(upstreamOfdmaData, sampleTime)

        # Store data to InfluxDB
        self.timeseriesWriter.write(record=downstreamPoints)
        self.timeseriesWriter.write(record=downstreamOfdmPoints)
        self.timeseriesWriter.write(record=upstreamPoints)
        self.timeseriesWriter.write(record=upstreamOfdmaPoints)

    def collectLogs(self):
        # Not implemented yet
        pass