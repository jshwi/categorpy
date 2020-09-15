"""
torrent
=======
"""
import argparse
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

import transmission_rpc

from categorpy.src import base
from categorpy.src.torrent import parse, find, scrape, data


def argument_parser(*_):
    """Parse the path selected for downloaded files, the torrent-dir
    to check for existing downloads and the url to scrape

    Collect the number argument for custom page numbers and ranges

    Determine whether running in `inspect` mode or whether downloads
    will be initialized

    :param _:   The sys.argv argument
    :return:    The instantiated ArgumentParser object to also use the
                print_help function along with the Namespace
    """
    module = base.COLOR.cyan.get("ctgpy torrent")
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(
        prog=module,
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog, max_help_position=55
        ),
    )
    parser.add_argument(
        "-p",
        "--path",
        action="store",
        help=(
            "fullpath to directory where conflict files may belong - if a "
            "path is not entered the last path given will be used"
        ),
    )
    parser.add_argument(
        "-t",
        "--torrent-dir",
        action="store",
        help="flag files currently downloading",
    )
    parser.add_argument(
        "-u",
        "--url",
        action="store",
        help=(
            "web address to scrape (needs to be run at least once to "
            "generate a cache)"
        ),
    )
    parser.add_argument(
        "-n",
        "--number",
        metavar="NUMBER or LOW-HIGH",
        action="store",
        help=(
            "search an alternative page number to the current selection or "
            "loop through a range of page numbers e.g. 1-4"
        ),
    )
    parser.add_argument(
        "-i",
        "--inspect",
        action="store_true",
        help=(
            "only information will be displayed and a download will not begin"
        ),
    )
    return parser


def read_saved(key):
    """Return the last value from the history file's json object
    matching the key

    :param key: History key to search
    :return:    The key's value
    """
    textio = base.TextIO(base.HISTORY)
    textio.read_json()
    return textio.object[key][-1]


def read_saved_args(args, key, print_help):
    """Parse the history file for the last entry added to the json
    object

    If no history has been recorded notify the user and print the
    argparse help

    :param args:        argparse Namespace class
    :param key:         Key to return from history
    :param print_help:  argparse print help function
    :return:            Path from history
    """
    if not args.__dict__[key]:
        try:
            return read_saved(key)
        except (FileNotFoundError, KeyError):
            with redirect_stdout(sys.stderr):
                base.COLOR.red.print(
                    f"you have no history of searches for `{key}' argument",
                )
                print_help()
            sys.exit(1)
    return args.__dict__[key]


def start_transmission(magnets, unmatched, highlight, **kwargs):
    """Compare magnet files parsed from bencode text into plaintext
    against existing files on the user's system

    If the `matched_magnets` list has been populated announce to the
    user the files which have begun downloading

    Announce to user if no new files can be downloaded from the scrape

    :param magnets:     List of magnet contents (not paths)
    :param unmatched:   List of torrents that have been scraped and are
                        not owned (in plaintext)
    :param highlight:   Draw attention to message with colored or plain
                        decorator (depending on whether running in gui
                        mode)
    :param kwargs:      Keyword args for the `transmission_rpc` client
                        All blank values as of now to run with defaults
    """
    parsed = parse.parse_magnets(magnets)
    unowned_magnets = [p for p in parsed if p in unmatched]
    if unowned_magnets:
        client = transmission_rpc.Client(**kwargs)
        for magnet in magnets:
            client.add_torrent(magnet)
        base.COLOR.cyan.bold.print(
            "The Following Unmatched Torrents Have Just Been Added:",
        )
        print("- \n- ".join(unmatched))
    else:
        print(f"{highlight}There's Nothing to Add{highlight}")


def initialize_index(scraper, torrent_dir):
    """Gather lists of several categories of files that we do not want
    the scraper to add to the torrent client

        - system files:         Any files that already exist on the
                                system
        - files downloading:    Parse torrent files for their name and
                                determine that this file has already
                                been added to the torrent client
        - blacklisted files:    Files or regular expressions added to
                                the `blacklist` file
        - packaged torrents:    Torrents that have been downloaded as
                                part of a directory, but are not in that
                                directory anymore

    Once a list comprised of unmatched files have been scraped and
    filtered either begin downloading the torrents or inspect the
    results of a session with the `inspect` argument

    Write reports in color to be viewed with this package or in
    plaintext to be viewed individually

    :param torrent_dir:
    :param scraper:
    """

    # get list of system files
    system = Path(os.path.expanduser("~"))
    syslist = system.rglob("*")
    files = [os.path.basename(str(f)) for f in syslist]

    # get list of files currently downloading
    parse_torrents = parse.ParseTorrents(torrent_dir)

    # get list of commented blacklisted files
    blist = data.ParseDataFile(base.BLACKLIST, scraper.names)
    blacklist = [f"{k}  # {v}" if v else k for k, v in blist.dataobj.items()]

    # get list of files in a pack
    # TODO automate this
    #  get download path from settings.json and looks for directories
    pack = parse.parse_file(base.PACK)

    # instantiate fuzzy find class with all the lists to match against
    # print report and cache report files
    # get list of unmatched files that can be downloaded
    return find.FuzzyFind(blacklist, parse_torrents.obj, files, pack)


def torrent_proc(fuzzy_find, scraper, url, inspect, gui):
    hlight = "***"  # just something to draw the user's attention

    # if not running in gui mode then it is ok to use ascii escape codes
    hlight, index_ = (hlight, 0) if gui else (base.COLOR.red.get(hlight), 1)
    report = fuzzy_find.report(url, scraper.names)[index_]

    if inspect:
        # print report and do not initialize any downloads
        # announce that this is happening
        print(report)
        print(f"{hlight}Nothing Added. Inspecting Only{hlight}")
    else:
        # initialize downloads for unmatched files
        # announce files added to the client
        # do not print report - too much text for multiple scrapes
        # the report can be viewed by running the report argument
        start_transmission(scraper.magnets, fuzzy_find.unmatched(), hlight)

    # write history to json
    textio = base.TextIO(base.HISTORY, sort=False)
    textio.append_json_array(("url", url))


def main(argv, gui=False):
    """Single run or loop the torrent process

    Collect args and persistent data (previous searched paths and urls)

    :param argv: Args passed from categorpy.src.main in submodules
    :param gui: Gui mode will be initialized as True when the gui is
                running , otherwise this will print usual ascii escape
                codes to the terminal
    """
    parser = argument_parser(*argv)
    args = parser.parse_args()

    # get persistent values for path and url used previously for running
    # torrent if these args are not provided
    url = read_saved_args(args, "url", parser.print_help)

    # ParsePageNumber will return a page number parsed from the url
    # and a True or False value for whether a page number exists
    parse_pages = parse.ParsePageNumber(url)

    # get last used page number if no page number argument has been
    # supplied
    number = args.number
    if not number:
        number = parse_pages.get_page_number()

    # scrape the web for magnets and their names
    scraper = scrape.ScrapeWeb(url)
    scraper.scrape_names(base.HTTP)
    scraper.scrape_magnets(base.MAGNET)

    fuzzy_find = initialize_index(scraper, args.torrent_dir)

    # split numbers for a range (if a range is given) otherwise nothing
    # happens here and the single digit remains the same
    # unpack tuple of low and high numbers
    # multiple runs for a start and stop, otherwise this will run only
    # once for two values of `0`
    numbers = number.split("-")
    stopint = 1 if len(numbers) > 1 else 0
    start, stop = int(numbers[0]), int(numbers[stopint]) + 1
    for i in range(start, stop):
        if parse_pages.ispage:
            url = parse_pages.select_page_number(i)
        torrent_proc(fuzzy_find, scraper, url, args.inspect, gui)
