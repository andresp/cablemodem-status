import configparser
import threading
from influxdb_client import InfluxDBClient
import logging
import logging_loki
from requests.packages import urllib3
import schedule
import time
from docsismodem.modems.observablemodemfactory import ObservableModemFactory

from flask import Flask
from flask_healthz import healthz

from docsismodem.probe import Probe
from docsismodem.collectionJob import collectionJob

def main():
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

    influxUrl =  ("https" if influxUseTLS else "http") + "://" + influxHost + ":" + influxPort

    modem = ObservableModemFactory.get(config['General']['ModemType'], config, consoleLogger)

    jobRunner = collectionJob(modem, config['Modem'].getboolean('CollectLogs'), consoleLogger)

    # Because the modem uses a self-signed certificate and this is expected, disabling the warning to reduce noise.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def runDaemon():
        jobRunner.collectionJob()
        consoleLogger.info("Running as daemon")
        schedule.every(runEveryMinutes).minutes.do(jobRunner.collectionJob)

        if enableHealthProbe is True:
            while 1:
                schedule.run_pending()
                time.sleep(1)
 
    if runAsDaemon:
        runnerThread = threading.Thread(target=runDaemon, daemon=True)
        runnerThread.start()
        if enableHealthProbe is True:
            create_flask_app(jobRunner)
        else:
            while 1:
                schedule.run_pending()
                time.sleep(1)
    else:
        consoleLogger.info("One-time execution")
        jobRunner.collectionJob()



def create_flask_app(runner):

    app = Flask(__name__)
    app.register_blueprint(healthz, url_prefix="/healthz")

    probe = Probe(runner, runEveryMinutes)

    app.config.update(
        HEALTHZ = {
            "live": probe.liveness,
            "ready": lambda: None,
        }
    )

    app.run(host='0.0.0.0', port=80, debug=False, use_reloader=False) 

class CustomTimestampFilter(logging.Filter):
    def filter(self, record):
        if hasattr(record, 'timestamp'):
            record.created = record.timestamp
        return True

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

lokiUrl = config['Loki']['Url']
lokiUsername = config['Loki']['Username']
lokiPassword = config['Loki']['Password']

runAsDaemon = config['General'].getboolean('Daemon')
enableHealthProbe = config['General'].getboolean('EnableK8sProbe')
runEveryMinutes = int(config['General']['RunEveryMinutes'])

lastUpdated = 0

if __name__ == '__main__':
    main()