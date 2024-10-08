import logging
from docsismodem.modems.observablemodem import ObservableModem
from docsismodem.modems.observablemodemfactory import ObservableModemFactory

from tests.test_mocks import config

class TestTouchstoneTG3492UPCCH:
    
    def test_init(self):
        
        instance = ObservableModemFactory.get("TouchstoneTG3492UPCCH", config, logging.getLogger(None))
        assert isinstance(instance, ObservableModem)
