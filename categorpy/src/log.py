"""
categorpy.src.log
=================

Logging functions and classes.
"""
import contextlib
import logging
import logging.handlers
import os
import time

from . import locate


class StreamLogger:
    """Run as a context class using ``with`` to capture output stream"""

    def __init__(self, name=locate.APPNAME, level="DEBUG", error=False):
        self.logger = get_logger("error") if error else get_logger()
        self.logger = logging.getLogger(name)
        self.name = self.logger.name
        self.level = getattr(logging, "ERROR" if error else level)
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


class Time:
    """Add a timer for logging processes"""

    def __init__(self):
        self.clock = time.process_time()
        self.elapsed = 0
        self.hours = 0
        self.mins = 0
        self.secs = 0

    def reset(self):
        """Reset the timer to now"""
        self.clock = time.process_time()

    def record(self):
        """Record the elapsed time since instantiated or since reset has
        been called
        """
        self.elapsed = round(time.process_time() - self.clock)
        self.mins, self.secs = divmod(self.elapsed, 60)
        self.hours, self.mins = divmod(self.mins, 60)


def log_time(proc_msg, function, **kwargs):
    """Run a method and include logging information:

        - announce the process has started
        - Log the process
        - Record the start and stop time and log this

    :param proc_msg:    The announcement to communicate the beginning
                        of the process
    :param function:    The function to be called
    :key args:          Any args the function may need - None is OK
    :key kwargs:        Any kwargs the function may need - None is OK
    :return:            Anything returned from the function
    """
    logger = logging.getLogger(locate.APPNAME)
    timer = Time()
    announce = f"{proc_msg}..."
    print(announce)
    logger.info(announce)
    returns = function(*kwargs.get("args", ()), **kwargs.get("kwargs", {}))
    timer.record()
    logger.info(
        "%s took: %sh %sm %ss", proc_msg, timer.hours, timer.mins, timer.secs
    )
    return returns


def make_logger(name=locate.APPNAME, debug=False):
    """Instantiate the global logging object containing several
    combined characteristics
    Create logging dir if one doesn't exist already
    Ensure all loggers contain the format "/$logdir/$logname"
    Ensure all loggers either display just the message or
    date-time, loglevel, message
    Ensure all loggers are configured to handle rotating logs
    Do not print logs to stdout or stderr

    :param name:            Name of the logger for ``logging.GetLogger``
    :param debug:           Debug mode: True or False
    """
    logfile = os.path.join(locate.APPDIRS.user_log_dir, f"{name}.log")
    logger = logging.getLogger(name)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    filehandler = logging.handlers.WatchedFileHandler(logfile)
    filehandler.setFormatter(formatter)
    loglevel = logging.DEBUG if debug else logging.INFO
    logger.setLevel(loglevel)
    logger.addHandler(filehandler)


def get_logger(name=locate.APPNAME):
    """Get logger with default being the appname, the other logger and
    logfile will generally be ``error``

    :param name:    The name of the already created logger
    :return:        ``logging.Logger`` object
    """
    return logging.getLogger(name)


def initialize_loggers(debug=False):
    """Initialize the loggers that can be retrieved with
    logging.getLogger(<name>)``.

    :param debug: Log debug messages: True or False
    """
    make_logger(debug=debug)
    make_logger(name="error", debug=debug)
    make_logger(name="transmission", debug=debug)
