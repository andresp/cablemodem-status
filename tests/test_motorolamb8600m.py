import logging
from docsismodem.modems.motorola_mb8600 import MotorolaMB8600
from docsismodem.modems.observablemodem import ObservableModem
from docsismodem.modems.observablemodemfactory import ObservableModemFactory


class TestMotorolaMB8600:

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
        
        instance = ObservableModemFactory.get("MotorolaMB8600", self.mockConfig, logging.getLogger(None))
        assert isinstance(instance, ObservableModem)
        assert type(instance) is MotorolaMB8600

