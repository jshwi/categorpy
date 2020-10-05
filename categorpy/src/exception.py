"""
exception
=========

Handle exceptions for the package

If exception is not fatal display a summary and log the rest to file

If fatal display a cleaner summary and log the stack-trace to file
"""
import sys

from . import log, locate


class AppErrs:
    """Class to display summary of exception and exit with chosen code

    Configure what will be logged to file

    :param header:  What will be display to stdout
    :param name:      The name of the logger
    :param level:     The logging level
    :param code:      The exit code
    """

    def __init__(self, header, name="error", level="exception", code=1):
        self.header = header
        self.name = name
        self.level = level
        self.code = code
        self.logger = log.get_logger(self.name)
        self.sendto = sys.stderr if self.code else sys.stdout

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
        "Process Terminated", name=locate.APPNAME, level="debug", code=0
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
