"""
parser
======

Commandline arguments parsed here
"""
import argparse
import sys
from contextlib import redirect_stdout


class Parser(argparse.ArgumentParser):
    """Parse the path selected for downloaded files, the torrent-dir
    to check for existing downloads and the url to scrape

    Collect the number argument for custom page numbers and ranges

    Determine whether running in `inspect` mode or whether downloads
    will be initialized
    """

    def __init__(self, history):
        # noinspection PyTypeChecker
        super().__init__(
            prog=f"\u001b[0;36;40mcategorpy\u001b[0;0m",
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
        self.history = history
        self._add_arguments()
        self.args = self.parse_args()
        self._parse_url()

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

    def _parse_url(self):
        """Parse the history file for the last entry added to the json
        object

        If no history has been recorded notify the user and print the
        argparse help
        :return: Path from history
        """
        if not self.args.url:
            try:
                self.history.read_json()
                self.args.__dict__["url"] = self.history.object["url"][-1]
            except (FileNotFoundError, KeyError):
                with redirect_stdout(sys.stderr):
                    print(f"\u001b[0;31;40myou have no url history\u001b[0;0m")
                    self.print_help()
                sys.exit(1)
