import logging
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from .timeserieswriter import TimeseriesWriter

class InfluxDB(TimeseriesWriter):

    dbClient = None
    logger = None
    bucket = ""

    def __init__(self, url: str, org: str, token: str, bucket: str, useTls: bool = True):
        self.bucket = bucket

        self.logger = logging.getLogger("influxdb")

        self.logger.info("Connecting to InfluxDB " + url + ", org: " + org + ". Using TLS? " + str(useTls))
        self.dbClient = InfluxDBClient(url=url, org=org, token=token, ssl=useTls)

        return
    
    def write(self, record: list):
        self.dbClient.write_api(write_options=SYNCHRONOUS).write(bucket=self.bucket, record=record)
