from abc import ABC, abstractmethod

from storage.timeserieswriterfactory import TimeseriesWriterFactory

class ObservableModem(ABC):

    config = None
    hostTimeZone = ""
    logger = None
    logTimeZone = ""
    timeseriesWriter = None

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

        self.logTimeZone = config['Modem']['LogTimezone']
        self.hostTimeZone = config['General']['HostTimezone']

        self.timeseriesWriter = TimeseriesWriterFactory.get(type="InfluxDB", config=config)

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
