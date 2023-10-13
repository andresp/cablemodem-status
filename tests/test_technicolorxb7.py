import logging
from docsismodem.modems.observablemodem import ObservableModem
from docsismodem.modems.observablemodemfactory import ObservableModemFactory
from docsismodem.modems.technicolor_xb7 import TechnicolorXB7


class TestTechnicolorXB7:

    mockConfig = {
        'Database': {
            'Bucket': 'testBucket',
            'Org': 'org',
            'Host': 'localhost',
            'Port': '443',
            'UseTls': True,
            'Token': 'token'
        },
        'General': {
            'HostTimezone': 'Pacific/Los_Angeles'
        },
        'Modem': {
            'Host': '10.0.0.1',
            'LogTimezone': 'Pacific/Los_Angeles'
        }
    }

    def test_init(self):
        
        instance = ObservableModemFactory.get("TechnicolorXB7", self.mockConfig, logging.getLogger(None))
        assert isinstance(instance, ObservableModem)
        assert type(instance) is TechnicolorXB7

