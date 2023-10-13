from abc import ABC, abstractmethod, abstractproperty
from influxdb_client.client.write_api import SYNCHRONOUS

class ObservableModem(ABC):

    config = None
    hostTimeZone = ""
    logger = None
    logTimeZone = ""
    influxBucket = ""
    writeApi = None

    def __init__(self, config, dbClient, logger):
        self.config = config
        self.logger = logger

        self.logTimeZone = config['Modem']['LogTimezone']
        self.hostTimeZone = config['General']['HostTimezone']
        self.influxBucket = config['Database']['Bucket']

        self.write_api = dbClient.write_api(write_options=SYNCHRONOUS)

        super().__init__()

    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def collectStatus(self):
        pass

    @abstractmethod
    def collectLogs(self):
        pass
