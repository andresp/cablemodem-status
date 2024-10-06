import logging
from docsismodem.modems.observablemodem import ObservableModem
from docsismodem.modems.observablemodemfactory import ObservableModemFactory

from tests.test_mocks import config

class TestMotorolaMB8600:

    def test_init(self):
        
        instance = ObservableModemFactory.get("MotorolaMB8600", config, logging.getLogger(None))
        assert isinstance(instance, ObservableModem)
