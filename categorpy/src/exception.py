"""
exception
=========

Handle exceptions for the package

If exception is not fatal display a summary and log the rest to file

If fatal display a cleaner summary and log the stack-trace to file
"""
import logging
import sys

from . import locate


class AppErrs:
    """Class to display summary of exception and exit with chosen code

    Configure what will be logged to file

    :param header:  What will be display to stdout
    :key name:      The name of the logger
    :key level:     The logging level
    :key sendto:    Where to direct the exception stream
    :key code:      The exit code
    """

    def __init__(self, header, **kwargs):
        self.header = header
        self.name = kwargs.get("name", "error")
        self.logger = logging.getLogger(self.name)
        self.level = kwargs.get("level", "exception")
        self.sendto = kwargs.get("sendto", sys.stderr)
        self.code = kwargs.get("code", 1)

    def summary(self, body=None):
        """Summary to be displayed to console

        :param body:    The main section of the summary if argument
                        passed else None
        """
        body = f"\n{body}" if body else ""
        print(
            f"\n\u001b[0;31;40m{self.header}\u001b[0;0m{body}",
            file=self.sendto,
        )

    def log(self, msg, **kwargs):
        """Log to file

        :param msg:     Heading for log
        :param kwargs:  Kwargs for logging module
        """
        method = getattr(self.logger, self.level)
        method(msg, **kwargs)
        sys.exit(self.code)


def exit_max_auth(tally):
    """Exit the process if too many incorrect password attempts have
    been made

    :param tally:   Log the amount of incorrect attempts that have been
                    made
    """
    apperrs = AppErrs("Too many incorrect password attempts", level="error")
    apperrs.summary(
        "please update your password in `transmission-daemon' settings.json "
        "and try again",
    )
    apperrs.log(tally)


def exit_fatal(err):
    """Exit if fatal error indicates ``transmission-rpc`` cannot be run

    :param err: The error that was raised
    """
    apperrs = AppErrs("Fatal error")
    apperrs.summary(
        "the process could not continue\n"
        "`transmission-daemon' may not be configured correctly\n"
        "please check logs for more information",
    )
    apperrs.log(str(err))


def terminate_proc():
    """Terminate the process"""
    apperrs = AppErrs(
        "Process Terminated",
        name=locate.APPNAME,
        level="debug",
        sendto=sys.stdout,
        code=0,
    )
    apperrs.summary()
    apperrs.log(apperrs.header, exc_info=True)


def exit_error(err):
    """Exit for a more generic error

    :param err: The error that was raised
    """
    apperrs = AppErrs(str(err), name="error")
    apperrs.summary()
    apperrs.log(apperrs.header)
