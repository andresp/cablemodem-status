import logging
from docsismodem.modems.observablemodem import ObservableModem
from docsismodem.modems.observablemodemfactory import ObservableModemFactory
from docsismodem.modems.technicolor_xb7 import TechnicolorXB7

from tests.mocks import config

class TestTechnicolorXB7:

    def test_init(self):
        
        instance = ObservableModemFactory.get("TechnicolorXB7", config, logging.getLogger(None))
        assert isinstance(instance, ObservableModem)
        assert type(instance) is TechnicolorXB7

