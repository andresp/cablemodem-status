import datetime
from collectionJob import collectionJob
from flask_healthz import HealthError


class Probe():

    runner = None
    runEveryMinutes = 0

    def __init__(self, runner: collectionJob, runEveryMinutes: int) -> None:
        self.runner = runner
        self.runEveryMinutes = runEveryMinutes

    def liveness(self):
        if datetime.datetime.now() - self.runner.lastCompletedTime() < datetime.timedelta(minutes=self.runEveryMinutes):
            pass
        else:
            raise HealthError("Health check did not pass.")

