from abc import ABC, abstractmethod, abstractproperty

class ObservableModem(ABC):

    config = None
    dbClient = None
    hostTimeZone = ""
    logger = None
    logTimeZone = ""

    def __init__(self, config, dbClient, logger):
        self.config = config
        self.dbClient = dbClient
        self.logger = logger

        self.logTimeZone = config['Modem']['LogTimezone']
        self.hostTimeZone = config['General']['HostTimezone']

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
