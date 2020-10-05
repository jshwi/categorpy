"""
parser
======

Parse commandline arguments
"""
import argparse
import sys
from contextlib import redirect_stdout

from . import locate, log, textio


class Parser(argparse.ArgumentParser):
    """Parse the path selected for downloaded files, the torrent-dir
    to check for existing downloads and the url to scrape

    Collect the number argument for custom page numbers and ranges

    Determine whether running in `inspect` mode or whether downloads
    will be initialized
    """

    def __init__(self):
        # noinspection PyTypeChecker
        super().__init__(
            prog="\u001b[0;36;40mcategorpy\u001b[0;0m",
            description=(
                "Run with no arguments to scrape the last entered url and "
                "begin seeding with `transmission-daemon'. Tweak the page "
                "number of the url history with the `page' argument - enter "
                "either a single page number or a range. If no url has been "
                "supplied prior, however, the program will not be able to run "
                "without the `url' argument followed by the url you wish to "
                "scrape. "
            ),
            formatter_class=lambda prog: argparse.HelpFormatter(
                prog, max_help_position=55
            ),
        )
        self._add_arguments()
        self.args = self.parse_args()

    def _add_arguments(self):
        self.add_argument(
            "-n",
            "--dry",
            action="store_true",
            help=(
                "only information will be displayed and a download will not "
                "begin"
            ),
        )
        self.add_argument(
            "-u",
            "--url",
            metavar="HISTORY",
            action="store",
            help="scrape new url or the last url entered",
        )
        self.add_argument(
            "-p",
            "--page",
            metavar="INT or START-END",
            action="store",
            help="scrape a single digit page number or a range e.g. 1-5",
        )


def parse_url(argparser):
    """Parse the history file for the last entry added to the json
    object. If no history has been recorded notify the user and print
    the argparse help.

    :param argparser:   ``argparse.ArgumentParser`` ``Namespace`` which
                        contains the ``url`` parameter and the
                        ``print_help`` method
    :return:            Url to scrape for torrents
    """
    history = textio.TextIO(locate.APPFILES.histfile, sort=False)

    history.read_json()

    try:
        url = history.object["history"][-1]["url"]
        textio.record_hist(history, url)
        return url
    except (FileNotFoundError, KeyError):
        logger = log.get_logger()
        with redirect_stdout(sys.stderr):
            announce = "you have no search history"
            print(f"\u001b[0;31;40m{announce}\u001b[0;0m")
            argparser.print_help()
        logger.exception(announce)
        sys.exit(1)


def get_namespace(argparser):
    """Complete the ``argparse`` ``Namespace`` object by populating the
    ``url`` object if one needs to be populated and one can be populated
    (else raise error) then return the ``Namespace`` object from
    ``argparse``

    :param argparser:   Instantiated ``argparse.ArgumentParser`` object
                        for commandline arguments
    :return:            Instantiated ``argparse.Namespace`` object for
                        commandline arguments
    """
    if not argparser.args.url:
        argparser.args.url = parse_url(argparser)

    return argparser.args
