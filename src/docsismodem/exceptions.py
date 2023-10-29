class ModemConnectionError(Exception):
    def __init__(self, message="An error occurred loging into the modem."):
        self.message = message
        super().__init__(self.message)

class ModemCredentialsError(Exception):
    def __init__(self, message="An error occurred loging into the modem."):
        self.message = message
        super().__init__(self.message)