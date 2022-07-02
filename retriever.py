from bs4 import BeautifulSoup
import configparser
import functools
from influxdb_client import InfluxDBClient
import logging
import logging_loki
import pytz
import requests
from requests.packages import urllib3
import schedule
import time
from modems.netgear_cm2000 import NetgearCM2000
from modems.technicolor_xb7 import TechnicolorXB7
from modems.motorola_mb8600 import MotorolaMB8600
from modems.touchstone_tg3492_upc_ch import TouchstoneTG3492UPCCH

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

@catch_exceptions(cancel_on_failure=False)
def collectionJob(modem):

    modem.collectStatus()

    if collectLogs:
        modem.collectLogs()

    consoleLogger.info("Done collecting status and logs")

# Init logger
logging.basicConfig(level=logging.INFO)
consoleLogger = logging.getLogger("app")

# Read configuration
consoleLogger.info("Reading configuration")

config = configparser.ConfigParser()
config.read('data/configuration.ini')

influxOrg = config['Database']['Org']
influxHost = config['Database']['Host']
influxPort = config['Database']['Port']
influxToken = config['Database']['Token']
influxUseTLS = bool(config['Database']['UseTls'])

collectLogs = config['Modem'].getboolean('CollectLogs')

lokiUrl = config['Loki']['Url']
lokiUsername = config['Loki']['Username']
lokiPassword = config['Loki']['Password']

runAsDaemon = config['General'].getboolean('Daemon')
runEveryMinutes = int(config['General']['RunEveryMinutes'])

consoleLogger.info("Connecting to InfluxDB")

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

influxUrl = "https://" + influxHost + ":" + influxPort

dbClient = InfluxDBClient(url=influxUrl, org=influxOrg, token=influxToken, ssl=influxUseTLS)

modems = {
    "MotorolaMB8600": MotorolaMB8600(config, dbClient, consoleLogger),
    "NetgearCM2000": NetgearCM2000(config, dbClient, consoleLogger),
    "TechnicolorXB7": TechnicolorXB7(config, dbClient, consoleLogger),
    "TouchstoneTG3492UPCCH": TouchstoneTG3492UPCCH(config, dbClient, consoleLogger)
}

# Because the modem uses a self-signed certificate and this is expected, disabling the warning to reduce noise.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

modem = modems[config['General']['ModemType']]
modem.login()

if runAsDaemon:
    collectionJob(modem)
    consoleLogger.info("Running as daemon")
    schedule.every(runEveryMinutes).minutes.do(collectionJob, modem)

    while 1:
        schedule.run_pending()
        time.sleep(1)
else:
    consoleLogger.info("One-time execution")
    collectionJob(modem)