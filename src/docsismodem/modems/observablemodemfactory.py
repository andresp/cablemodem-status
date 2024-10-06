from .modemtype import ModemType
from .hitron_coda56 import HitronCoda56
from .motorola_mb8600 import MotorolaMB8600
from .netgear_cm2000 import NetgearCM2000
from .observablemodem import ObservableModem
from .technicolor_xb7 import TechnicolorXB7
from .touchstone_tg3492_upc_ch import TouchstoneTG3492UPCCH

class ObservableModemFactory():
    @staticmethod
    def get(type: ModemType, config, logger) -> ObservableModem:

        match type:
            case ModemType.MotorolaMB8600:
                return MotorolaMB8600(config, logger)
            case ModemType.NetgearCM2000:
                return NetgearCM2000(config, logger)
            case ModemType.TechnicolorXB7:
                return TechnicolorXB7(config, logger)
            case ModemType.TouchstoneTG3492UPCCH:
                return TouchstoneTG3492UPCCH(config, logger)
            case ModemType.HitronCoda56:
                return HitronCoda56(config, logger)
            case _:
                raise ValueError("Invalid modem type selected.")
