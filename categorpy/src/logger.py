"""
logger
======

Package-wide logging
"""
import datetime
import logging
import logging.handlers
import os
import pathlib


class Logger:
    """Make loggers with tuple input for the loglevel and the
    filename
    """

    def __init__(self, logdir, loglevel):
        self.logdir = logdir
        self.path = pathlib.Path(logdir)
        self.loglevel = loglevel
        self.date = datetime.date.today().strftime("%Y-%m-%d")
        self.make_logdir()
        self.make_logger()

    def make_logger(self):
        """Instantiate the global logging object containing several
        combined characteristics
        Create logging dir if one doesn't exist already
        Ensure all loggers contain the format "/$logdir/$logname"
        Ensure all loggers either display just the message or
        date-time, loglevel, message
        Ensure all loggers are configured to handle rotating logs
        Do not print logs to stdout or stderr
        """
        logfile = os.path.join(self.logdir, f"{self.loglevel}-{self.date}.log")
        logger = logging.getLogger(self.loglevel)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)-8s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        filehandler = logging.handlers.WatchedFileHandler(logfile)

        filehandler.setFormatter(formatter)

        logger.setLevel(logging.INFO)

        logger.addHandler(filehandler)

    def log(self, **kwargs):
        """Call a made logger with loglevel as the first argument and
        ``logging`` kwargs thereafter

        :param kwargs:      kwargs to pass to ``logging``
        """
        logger = logging.getLogger(self.loglevel)
        try:
            level = getattr(logger, self.loglevel)
        except AttributeError:
            level = getattr(logger, "info")
        kwargs["msg"] = kwargs.get("msg", "")
        level(**kwargs)

    def write(self, msg):
        """Will be called when used as a contextlib action

        :param msg: The message to log - stdout stream
        """
        if msg and not msg.isspace():
            self.log(loglevel="info", msg=msg)

    def make_logdir(self):
        """Make sure a log directory exists"""
        self.path.mkdir(parents=True, exist_ok=True)

    def flush(self):
        """For when we are capturing stdout or stderr"""
        pass  # pylint: disable=W0107
