import logging
from docsismodem.modems.observablemodem import ObservableModem
from docsismodem.modems.observablemodemfactory import ObservableModemFactory
from docsismodem.modems.touchstone_tg3492_upc_ch import TouchstoneTG3492UPCCH


class TestTouchstoneTG3492UPCCH:

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
        
        instance = ObservableModemFactory.get("TouchstoneTG3492UPCCH", self.mockConfig, logging.getLogger(None))
        assert isinstance(instance, ObservableModem)
        assert type(instance) is TouchstoneTG3492UPCCH

