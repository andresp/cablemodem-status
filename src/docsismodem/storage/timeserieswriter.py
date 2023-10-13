from abc import ABC, abstractmethod

class TimeseriesWriter(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def write(self, record: list):
        pass