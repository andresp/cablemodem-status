from .influxdb import InfluxDB
from .storagetype import StorageType

class TimeseriesWriterFactory():

    @staticmethod
    def get(type: StorageType, config: list):
        match type:
            case StorageType.InfluxDB:
                org = config['Database']['Org']
                host = config['Database']['Host']
                port = config['Database']['Port']
                token = config['Database']['Token']
                bucket = config['Database']['Bucket']
                useTls = config['Database'].getboolean('UseTls')
                url =  ("https" if useTls else "http") + "://" + host + ":" + port

                return InfluxDB(url, org, token, bucket, useTls)
            
            case _:
                raise ValueError("Invalid StorageType specified.")

