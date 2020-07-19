"""
main
====

The entire package's main
"""
import contextlib
import os
import sys

import appdirs
import object_colors
import transmission_rpc

from . import config, find, files, logger, parser, style, system, textio, web

APPNAME = "categorpy"
COLOR = object_colors.Color()

# --- user appdirs ---
CACHEDIR = appdirs.user_cache_dir(APPNAME)
DATADIR = appdirs.user_data_dir(APPNAME)
CONFIGDIR = appdirs.user_config_dir(APPNAME)
LOGDIR = appdirs.user_log_dir(APPNAME)

# --- cache files ---
HISTORY = os.path.join(CACHEDIR, "history")
MAGNET = os.path.join(CACHEDIR, "magnets")

COLOR.populate_colors()


def log_fatal_error(hint):
    errlogger = logger.Logger(LOGDIR, loglevel="error")
    errlogger.log(exc_info=True)
    print(f"\n{COLOR.red.get('Fatal error')}\n{hint}", file=sys.stderr)
    sys.exit(1)


def start_transmission(magnets, unmatched, **kwargs):
    """Compare magnet files parsed from bencode text into plaintext
    against existing files on the user's system

    If the `matched_magnets` list has been populated announce to the
    user the files which have begun downloading

    Announce to user if no new files can be downloaded from the scrape

    :param magnets:     List of magnet contents (not paths)
    :param unmatched:   List of torrents that have been scraped and are
                        not owned (in plaintext)
    :param kwargs:      Keyword args for the `transmission_rpc` client
                        All blank values as of now to run with defaults
    """
    error_logger = logger.Logger(LOGDIR, loglevel="error")
    report_logger = logger.Logger(LOGDIR, loglevel="report")
    unowned_magnets = [v for k, v in magnets.items() if k in unmatched]
    if unowned_magnets:
        # noinspection PyBroadException
        try:
            with contextlib.redirect_stdout(error_logger):
                client = transmission_rpc.Client(**kwargs)
        except Exception:  # pylint: disable=W0703
            log_fatal_error(
                f"the process could not continue\n"
                f"`transmission-daemon' may not be configured correctly\n\n"
                f"please check {LOGDIR} for more information"
            )
        for magnet in unowned_magnets:
            client.add_torrent(magnet)
        newfiles = "- " + "\n- ".join(unmatched)
        info = (
            f"The Following Unmatched Torrents Have Just Been Added:"
            f"\n- {newfiles}\n"
        )
    else:
        info = "***There's Nothing to Add***\n"
    report_logger.log(msg=f"\n{info}")
    style.pygment_print(info)


def settings_obj():
    """Module entry point for ``settings.json``"""
    _config = config.Config(CONFIGDIR)

    _config.initialize_config()

    try:
        return _config.read_json()
    except FileNotFoundError:
        log_fatal_error(
            "`transmission-daemon' settings could not be found\n"
            f"please check {LOGDIR} for more information"
        )


def initialize_index(magnets):
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
    """
    # get list of commented blacklisted files
    blacklist = files.Saved(
        filename="blacklist", datadir=DATADIR, logdir=LOGDIR
    )
    blacklist.parse_blacklist(magnets)

    # get list of files in a pack
    pack = files.Saved(filename="pack", datadir=DATADIR, logdir=LOGDIR)
    pack.parse_file()

    obj = settings_obj()

    download_dir = obj["download-dir"]

    system_index = system.Index(download_dir, LOGDIR)

    # get list of files currently downloading
    torrents = files.Torrents(download_dir)
    torrents.parse_torrents()

    # instantiate fuzzy find class with all the lists to match against
    # print report and cache report files
    # get list of unmatched files that can be downloaded
    return find.Find(
        cachedir=CACHEDIR,
        logdir=LOGDIR,
        blacklisted=blacklist.obj,
        owned=system_index.files,
        downloading=torrents.obj,
        pack=pack.files,
    )


def rpc_kwargs():
    """Get rpc kwargs"""
    want = ["password", "username"]
    obj = settings_obj()
    return {k: obj[f"rpc-{k}"] for k in want}


def torrent_proc(fuzzy_find, names, obj, url, **kwargs):
    """Torrent process

    :param fuzzy_find:  Instantiated fuzzy-find object
    :param names:       Magnet names
    :param obj:         Magnet dictionary
    :param url:         Url to scrape
    :param kwargs:      kwargs for ``transmission`` i.e. username,
                        password
    """
    # match the above lists against the scraped files
    fuzzy_find.iterate(names, url)

    # initialize downloads for unmatched files
    # announce files added to the client
    # do not print report - too much text for multiple scrapes
    # the report can be viewed by running the report argument
    unmatched = fuzzy_find.filelist("unmatched", "list")
    start_transmission(obj, unmatched, **kwargs)


def intervals(pages):
    """ "Split numbers for a range (if a range is given) otherwise
    nothing happens here and the single digit remains the same
    unpack tuple of low and high numbers
    multiple runs for a start and stop, otherwise this will run only
    once for two values of `0`
    """
    numbers = pages.split("-")
    stopint = 1 if len(numbers) > 1 else 0
    return int(numbers[0]), int(numbers[stopint]) + 1


def main():
    """Single run or loop the torrent process

    Collect args and persistent data (previous searched paths and urls)
    """
    history = textio.TextIO(HISTORY, sort=False)
    argparser = parser.Parser(history)
    args = argparser.args
    url = args.url
    pages = args.pages
    parse_pages = files.PageNumbers(url)
    kwargs = rpc_kwargs()

    history.append_json_array(("url", url))

    try:
        print("Enumerating objects...")

        scraper = web.ScrapeWeb()
        pages = pages if pages else parse_pages.get_page_number()

        scraper.process_request(url)

        scraper.parse_magnets(MAGNET)

        fuzzy_find = initialize_index(scraper.names)
        start, stop = intervals(pages)

        for i in range(start, stop):
            if parse_pages.ispage:
                url = parse_pages.select_page_number(i)

            scraper.process_request(url)

            scraper.parse_magnets(MAGNET)

            torrent_proc(fuzzy_find, scraper.names, scraper.obj, url, **kwargs)
    except (KeyboardInterrupt, EOFError):
        print("\u001b[0;31;40mProcess Terminated\u001b[0;0m")
