"""
categorpy.src.main
==================
"""

import argparse
import sys
from contextlib import redirect_stdout

from . import client, find, locate, log, textio


class Parser(argparse.ArgumentParser):
    """Parse the path selected for downloaded files, the torrent-dir
    to check for existing downloads and the url to scrape. Collect the
    number argument for custom page numbers and ranges. Determine
    whether running in `inspect` mode or whether downloads will be
    initialized.
    """

    def __init__(self):
        # noinspection PyTypeChecker
        super().__init__(
            prog=f"\u001b[0;36;40m{locate.APP.appname}\u001b[0;0m",
            formatter_class=lambda prog: argparse.HelpFormatter(
                prog, max_help_position=55
            ),
        )
        self._add_arguments()
        self.args = self.parse_args()

    def _add_arguments(self):
        self.add_argument(
            "-u",
            "--url",
            action="store",
            help="scrape new url or the last url entered",
        )
        self.add_argument(
            "-c",
            "--cutoff",
            action="store",
            metavar="70",
            default="70",
            help=(
                "cutoff percentage when excluding torrents by word similarity"
            ),
        )
        self.add_argument(
            "--pages",
            metavar="PAGE or START-STOP",
            action="store",
            help="scrape a single digit page number or a range e.g. 1-5",
        )
        self.add_argument(
            "-d", "--debug", action="store_true", help=argparse.SUPPRESS
        )


def parse_url(argparser):
    """Parse the history file for the last entry added to the json
    object. If no history has been recorded notify the user and print
    the argparse help.

    :param argparser:   ``argparse.ArgumentParser`` ``Namespace`` which
                        contains the ``url`` parameter and the
                        ``print_help`` method.
    :return:            URL to scrape for torrents.
    """
    history = textio.TextIO(locate.APP.histfile, sort=False)
    history.read_json()
    try:
        url = history.object["history"][-1]["url"]
        textio.record_hist(history, url)
        return url
    except (FileNotFoundError, KeyError) as err:
        with redirect_stdout(sys.stderr):
            print("\u001b[0;31;40myou have no search history\u001b[0;0m")
            argparser.print_help()
        errlogger = log.get_logger("error")
        errlogger.exception(str(err))
        sys.exit(1)


def get_namespace(argparser):
    """Complete the ``argparse`` ``Namespace`` object by populating the
    ``url`` object if one needs to be populated and one can be populated
    (else raise error) then return the ``Namespace`` object from
    ``argparse``.

    :param argparser:   Instantiated ``argparse.ArgumentParser`` object
                        for commandline arguments.
    :return:            Instantiated ``argparse.Namespace`` object for
                        commandline arguments.
    """
    if not argparser.args.url:
        argparser.args.url = parse_url(argparser)

    return argparser.args


def main():
    """Begin by parsing commandline arguments and returning
    ``parser.Parser`` object. Get the ``INFO`` or ``DEBUG`` loglevel
    ``logger``, depending on the commandline arguments passed. Get the
    instantiated ``find.Find`` object containing the parsed blacklist
    and paths files as well as the indexed paths. Handle
    ``KeyboardInterrupt`` and ``EOFError`` for the main processes
    cleanly. Allow for ``KeyboardInterrupt`` and ``EOFError``
    stack-trace to be logged if running with
    ``argparser.args.debug is True``.
    """
    argparser = Parser()
    log.initialize_loggers(debug=argparser.args.debug)
    args = get_namespace(argparser)
    try:
        findobj = find.instantiate_find(args.cutoff)
        log.log_time(
            "Finding torrents", client.transmission, args=(args, findobj)
        )
    except (KeyboardInterrupt, EOFError) as err:
        print("\u001b[0;31;40mProcess Terminated\u001b[0;0m")
        errlogger = log.get_logger("error")
        errlogger.debug(str(err), exc_info=True)
