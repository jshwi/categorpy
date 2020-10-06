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


def make_logger(name, debug=False):
    """Instantiate the global logging object containing several
    combined characteristics. Create logging dir if one doesn't exist
    already. Ensure all loggers contain the format "/$logdir/$logname".
    Ensure all loggers either display just the message or date-time,
    loglevel, message. Ensure all loggers are configured to handle
    rotating logs. Do not print logs to stdout or stderr.

    :param name:    Name of the logger for ``logging.GetLogger``
    :param debug:   Debug mode: True or False
    """
    logfile = os.path.join(locate.APP.user_log_dir, f"{name}.log")
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


def initialize_loggers(debug=False):
    """Initialize the loggers that can be retrieved with
    logging.getLogger(<name>)``.

    :param debug: Log debug messages: True or False.
    """
    names = [locate.APP.appname, "error", "transmission"]
    for name in names:
        make_logger(name=name, debug=debug)


def get_logger(name=locate.APP.appname):
    """Get logger with default being the appname, the other logger and
    logfile will generally be ``error``.

    :param name:    The name of the already created logger.
    :return:        ``logging.Logger`` object.
    """
    return logging.getLogger(name)


class StreamLogger:
    """Run as a context class using ``with`` to capture output
    stream.
    """

    def __init__(self, name=locate.APP.appname):
        self.logger = get_logger(name)
        self._redirector = contextlib.redirect_stdout(self)

    def write(self, msg):
        """Will be called when used as a contextlib action.

        :param msg: The message to log - stdout stream.
        """
        if msg and not msg.isspace():
            self.logger.info(msg)

    def flush(self):
        """For when we are capturing stdout or stderr."""
        pass  # pylint: disable=W0107

    def __enter__(self):
        self._redirector.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # let contextlib do any exception handling here
        self._redirector.__exit__(exc_type, exc_val, exc_tb)


class Time:
    """Add a timer for logging processes."""

    def __init__(self):
        self._start = time.process_time()
        self.elapsed = 0

    def _get_units(self):
        mins, secs = divmod(self.elapsed, 60)
        hours, mins = divmod(mins, 60)
        return hours, mins, secs

    def reset(self):
        """Reset the clock"""
        self._start = time.process_time()

    def record(self):
        """Record the elapsed time since instantiated or since reset has
        been called.

        :return: Tuple containing hours, minutes and seconds
        """
        finish = time.process_time()
        self.elapsed = round(finish - self._start)
        return self._get_units()


def log_time(proc_msg, function, **kwargs):
    """Run a method and and log the process. Announce the message and
    time the length it took to complete the function. If the function
    returns a value return that too.

    :param proc_msg:    The announcement to communicate the beginning
                        of the process.
    :param function:    The function to be called.
    :key args:          Any args the function may need - None is OK.
    :key kwargs:        Any kwargs the function may need - None is OK.
    :return:            Anything returned from the function.
    """
    timer = Time()
    logger = get_logger()
    print(f"{proc_msg}...")
    logger.info(proc_msg)
    returns = function(*kwargs.get("args", ()), **kwargs.get("kwargs", {}))
    hours, mins, secs = timer.record()
    logger.info("%s took: %sh %sm %ss", proc_msg, hours, mins, secs)
    return returns
