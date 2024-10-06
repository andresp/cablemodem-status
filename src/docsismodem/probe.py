import datetime
from flask_healthz import HealthError
from collectionJob import CollectionJob

class Probe():

    runner = None
    runEveryMinutes = 0

    def __init__(self, runner: CollectionJob, runEveryMinutes: int) -> None:
        self.runner = runner
        self.runEveryMinutes = runEveryMinutes

    def liveness(self):
        if datetime.datetime.now() - self.runner.lastCompletedTime() < datetime.timedelta(minutes=self.runEveryMinutes * 2):
            pass
        else:
            raise HealthError("Health check did not pass.")

