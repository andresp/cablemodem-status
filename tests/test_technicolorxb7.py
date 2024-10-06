import logging

import pytest
import responses
from docsismodem.exceptions import ModemConnectionError, ModemCredentialsError
from docsismodem.modems.observablemodem import ObservableModem
from docsismodem.modems.observablemodemfactory import ObservableModemFactory

from tests.test_mocks import config

class TestTechnicolorXB7:

    def test_init(self):
        
        instance = ObservableModemFactory.get("TechnicolorXB7", config, logging.getLogger(None))
        assert isinstance(instance, ObservableModem)

    @responses.activate
    def test_succcessful_login(self):

        responses.add(responses.POST, f'http://{config["Modem"]["Host"]}/check.jst', json={}, status=302)
        
        instance = ObservableModemFactory.get("TechnicolorXB7", config, logging.getLogger(None))
        instance.login()

    @responses.activate
    def test_invalid_login(self):
        responses.add(responses.POST, f'http://{config["Modem"]["Host"]}/check.jst', json={}, status=200)
        
        instance = ObservableModemFactory.get("TechnicolorXB7", config, logging.getLogger(None))
        with pytest.raises(ModemCredentialsError):
            instance.login()

    def test_login_unreachable_modem(self):
        instance = ObservableModemFactory.get("TechnicolorXB7", config, logging.getLogger(None))
        with pytest.raises(ModemConnectionError):
            instance.login()