"""
logger
======

Package-wide logging
"""
import contextlib
import logging
import logging.handlers
import os


def make_logger(loglevel, logdir):
    """Instantiate the global logging object containing several
    combined characteristics
    Create logging dir if one doesn't exist already
    Ensure all loggers contain the format "/$logdir/$logname"
    Ensure all loggers either display just the message or
    date-time, loglevel, message
    Ensure all loggers are configured to handle rotating logs
    Do not print logs to stdout or stderr
    """
    logfile = os.path.join(logdir, f"{loglevel}.log")
    logger = logging.getLogger(loglevel)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    filehandler = logging.handlers.WatchedFileHandler(logfile)

    filehandler.setFormatter(formatter)

    logger.setLevel(logging.INFO)

    logger.addHandler(filehandler)


class StreamLogger:
    def __init__(self, loglevel):
        self.logger = logging.getLogger(loglevel)
        self.level = getattr(logging, loglevel)
        self._redirector = contextlib.redirect_stdout(self)

    def write(self, msg):
        """Will be called when used as a contextlib action

        :param msg: The message to log - stdout stream
        """
        if msg and not msg.isspace():
            self.logger.log(self.level, msg)

    def flush(self):
        """For when we are capturing stdout or stderr"""
        pass  # pylint: disable=W0107

    def __enter__(self):
        self._redirector.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # let contextlib do any exception handling here
        self._redirector.__exit__(exc_type, exc_val, exc_tb)
