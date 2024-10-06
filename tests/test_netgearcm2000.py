import logging
from docsismodem.modems.netgear_cm2000 import NetgearCM2000
from docsismodem.modems.observablemodem import ObservableModem
from docsismodem.modems.observablemodemfactory import ObservableModemFactory

from tests.test_mocks import config

class TestNetgear2000:

    def test_init(self):
        
        instance = ObservableModemFactory.get("NetgearCM2000", config, logging.getLogger(None))
        assert isinstance(instance, ObservableModem)
        assert type(instance) is NetgearCM2000

