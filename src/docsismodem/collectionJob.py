import datetime
import functools
from logging import Logger
from sched import scheduler
from .modems.observablemodem import ObservableModem

class collectionJob():

    modem = None
    collectLogs = False
    logger = None
    lastCompleted = datetime.datetime.now()

    def __init__(self, modem: ObservableModem, collectLogs: bool, logger: Logger):
        self.modem = modem
        self.collectLogs = collectLogs
        self.logger = logger

    def catch_exceptions(cancel_on_failure=False):
        def catch_exceptions_decorator(job_func):
            @functools.wraps(job_func)
            def wrapper(*args, **kwargs):
                try:
                    return job_func(*args, **kwargs)
                except:
                    import traceback
                    print(traceback.format_exc())
                    if cancel_on_failure:
                        return scheduler.CancelJob
            return wrapper
        return catch_exceptions_decorator

    @catch_exceptions(cancel_on_failure=False)
    def collectionJob(self):

        self.modem.login()

        self.modem.collectStatus()

        if self.collectLogs:
            self.modem.collectLogs()

        self.lastCompleted = datetime.datetime.now()
        self.logger.info("Done collecting status and logs")

    def lastCompletedTime(self):
        return self.lastCompleted
