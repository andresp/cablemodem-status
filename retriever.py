from bs4 import BeautifulSoup
import configparser
from datetime import datetime
from influxdb import InfluxDBClient
import re
import requests
from requests.packages import urllib3

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

def formatUpstreamQamPoints(data):
    points = []
    for row in data:
        point = {}
        point["measurement"] = "upstreamQam"
        point["tags"] = {}
        point["tags"]["channel"] = row[0]
        point["tags"]["lockStatus"] = row[1]
        point["tags"]["usChannelType"] = row[2]
        point["tags"]["channelId"] = int(row[3])
        point["tags"]["symbolRate"] = int(row[4])
        point["tags"]["frequency"] = row[5]
        point["time"] = sampleTime
        point["fields"] = {}
        point["fields"]["power"] = float(row[6].split()[0])
        points.append(point)

    return points

def formatUpstreamOFDMAPoints(data):
    points = []
    for row in data:
        point = {}
        point["measurement"] = "upstreamOFDMA"
        point["tags"] = {}
        point["tags"]["channel"] = row[0]
        point["tags"]["lockStatus"] = row[1]
        point["tags"]["modulation"] = row[2]
        point["tags"]["channelId"] = int(row[3])
        point["tags"]["frequency"] = row[4]
        point["time"] = sampleTime
        point["fields"] = {}
        point["fields"]["power"] = float(row[5].split()[0])
        points.append(point)

    return points

def formatDownstreamQamPoints(data):
    points = []
    for row in data:
        point = {}
        point["measurement"] = "downstreamQam"
        point["tags"] = {}
        point["tags"]["channel"] = row[0]
        point["tags"]["lockStatus"] = row[1]
        point["tags"]["modulation"] = row[2]
        point["tags"]["channelId"] = int(row[3])
        point["tags"]["frequency"] = row[4]
        point["time"] = sampleTime
        point["fields"] = {}
        point["fields"]["power"] = float(row[5].split()[0])
        point["fields"]["snr"] = float(row[6].split()[0])
        point["fields"]["correctables"] = int(row[7])
        point["fields"]["uncorrectables"] = int(row[8])
        points.append(point)

    return points

def formatDownstreamOFDMPoints(data):
    points = []
    for row in data:
        point = {}
        point["measurement"] = "downstreamOFDM"
        point["tags"] = {}
        point["tags"]["channel"] = row[0]
        point["tags"]["lockStatus"] = row[1]
        point["tags"]["modulation"] = row[2]
        point["tags"]["channelId"] = int(row[3])
        point["tags"]["frequency"] = row[4]
        point["time"] = sampleTime
        point["fields"] = {}
        point["fields"]["power"] = float(row[5].split()[0])
        point["fields"]["snr"] = float(row[6].split()[0])
        point["fields"]["subcarrierRange"] = row[7]
        point["fields"]["uncorrected"] = int(row[8])
        point["fields"]["correctables"] = int(row[9])
        point["fields"]["uncorrectables"] = int(row[10])
        points.append(point)

    return points

# Read configuration
config = configparser.ConfigParser()
config.read('configuration.ini')

influxDatabase = config['Database']['Name']
influxHost = config['Database']['Host']
influxPort = int(config['Database']['Port'])
influxUser = config['Database']['Username']
influxPassword = config['Database']['Password']

modemAuthentication = {
    "loginName": "admin",
    "loginPassword": config['Modem']['Password']
}

dbClient = InfluxDBClient(host=influxHost, port=influxPort, username=influxUser, password=influxPassword)
dbClient.switch_database(influxDatabase)

baseUrl = "https://" + config['Modem']['Host']

# Because the modem uses a self-signed certificate and this is expected, disabling the warning to reduce noise.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
response = session.get(baseUrl, verify=False)

# Get login url
loginPage = BeautifulSoup(response.content, features="lxml")

loginForm = loginPage.select("#target")
loginUrl = loginForm[0].get("action")

# Login
response = session.post(baseUrl + loginUrl, data=modemAuthentication, verify=False)

# Get status
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

    upstreamQamPoints = formatUpstreamQamPoints(upstreamQamChannels)
    downstreamQamPoints = formatDownstreamQamPoints(downstreamQamChannels)
    upstreamOFDMAPoints = formatUpstreamOFDMAPoints(upstreamOFDMAChannels)
    downstreamOFDMPoints = formatDownstreamOFDMPoints(downstreamOFDMChannels)

    # Store data to InfluxDB
    dbClient.write_points(upstreamQamPoints)
    dbClient.write_points(downstreamQamPoints)
    dbClient.write_points(upstreamOFDMAPoints)
    dbClient.write_points(downstreamOFDMPoints)