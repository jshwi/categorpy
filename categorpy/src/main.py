"""
main
====

The entire package's main
"""
import logging
import os
import pathlib
import sys

import appdirs
import transmission_rpc

from . import config, find, files, parser, textio, web

APPNAME = "categorpy"
CACHEDIR = appdirs.user_cache_dir(APPNAME)
CONFIGDIR = appdirs.user_config_dir(APPNAME)
LOGDIR = appdirs.user_log_dir(APPNAME)


def initialize_appdirs():
    """Create directories for persistent data storage for app"""
    dirs = [CACHEDIR, CONFIGDIR, LOGDIR]
    for _dir in dirs:
        path = pathlib.Path(_dir)
        path.mkdir(parents=True, exist_ok=True)


def initialize_loggers():
    """Initialize the loggers that can be retrieved with
    ``logging.getLogger(<name>)``
    """
    loglevels = ["debug", "info", "warning", "error"]
    for loglevel in loglevels:
        textio.make_logger(loglevel, LOGDIR)


def log_fatal_error(hint):
    """Log a non-verbose message to the terminal and log the traceback
    to a log file

    :param hint: Less verbose error hint
    """
    logger = logging.getLogger("error")
    logger.error("", exc_info=True)
    print(f"\u001b[0;31;40mFatal error\u001b[0;0m\n{hint}", file=sys.stderr)
    sys.exit(1)


def instantiate_client(**kwargs):
    """Attempt to instantiate the ``transmission_rpc.Client`` class or
    log an error and explain the nature of the fault to the user before
    exiting with a non-zero exit code

    :param kwargs:  Key-value settings read from the
                    ``transmission-daemon`` settings.json file
    :return:        Instantiated ``transmission_rpc.Client`` class
    """
    # noinspection PyBroadException
    try:
        with textio.StreamLogger("info"):
            return transmission_rpc.Client(**kwargs)
    except Exception:  # pylint: disable=W0703
        log_fatal_error(
            f"the process could not continue\n"
            f"`transmission-daemon' may not be configured correctly\n\n"
            f"please check {LOGDIR} for more information"
        )


def load_client(unowned_magnets, client):
    """Loop through the unowned magnets and load them into the
    instantiated ``transmission_rpc.Client`` class

    :param unowned_magnets: Magnets which are good to be downloaded
    :param client:          Instantiated ``transmission_rpc.Client``
                            class to call ``add_torrent`` with
    """
    for magnet in unowned_magnets:
        client.add_torrent(magnet)


def announce_added(unmatched):
    """Display the torrents that have just been added to the
    ``transmission-daemon`` client

    :param unmatched:   The unmatched torrents that have been added
    :return:            A single string spanning multiple lines to
                        announce what was added to the user
    """
    newfiles = "- " + "\n- ".join(unmatched)
    return (
        f"The Following Unmatched Torrents Have Just Been Added:\n"
        f"{newfiles}\n"
    )


def load_torrents(unowned_magnets, unmatched, **kwargs):
    """Load the magnet links into the rpc client

    :param unowned_magnets: Magnets not owned by user so good to load
    :param unmatched:       Unmatched human readable names of magnets
    :param kwargs:          Kwargs for the rpc client loaded from the
                            settings.json file in the
                            ``transmission-daemon`` config dir
    :return:                Info regarding what torrent were loaded into
                            client
    """
    client = instantiate_client(**kwargs)
    load_client(unowned_magnets, client)
    return announce_added(unmatched)


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
    logger = logging.getLogger("info")
    unowned_magnets = [v for k, v in magnets.items() if k in unmatched]
    info = "***There's Nothing to Add***\n"
    if unowned_magnets:
        info = load_torrents(unowned_magnets, unmatched, **kwargs)
    logger.info("\n%s", info)
    textio.pygment_print(info)


def attempt_read(_config):
    """Attempt to read the settings.json file belonging to
    ``transmission_daemon`` and return it as a dictionary object parsed
    with the ``json`` module

    :param _config: Instantiated ``config.Config`` class
    :return:        Dictionary of ``transmission-daemon`` settings.json
                    key-values
    """
    try:
        return _config.read_json()
    except FileNotFoundError:
        log_fatal_error(
            "`transmission-daemon' settings could not be found\n"
            f"please check {LOGDIR} for more information"
        )


def settings_obj():
    """Module entry point for ``settings.json``"""
    _config = config.Config(CONFIGDIR)

    _config.initialize_config()

    return attempt_read(_config)


def initialize_paths_file():
    paths = files.Saved(filename="paths", datadir=CONFIGDIR)
    filepath = paths.file
    filestatus = os.stat(filepath)
    if not filestatus.st_size:
        pathio = textio.TextIO(filepath)
        pathio.write(str(pathlib.Path.home()))
    paths.parse_file()
    return paths.files


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
    blacklist = files.Saved(filename="blacklist", datadir=CONFIGDIR)
    blacklist.parse_blacklist(magnets)

    # get list of files in a pack
    pack = files.Saved(filename="pack", datadir=CONFIGDIR)
    pack.parse_file()

    obj = settings_obj()

    download_dir = obj["download-dir"]

    paths = initialize_paths_file()
    idx = files.Index(paths)

    idx.iterate()

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
        owned=idx.files,
        downloading=torrents.obj,
        pack=pack.files,
    )


def rpc_kwargs():
    """Get rpc kwargs"""
    want = ["password", "username"]
    obj = settings_obj()
    return {k: obj[f"rpc-{k}"] for k in want}


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
    initialize_appdirs()

    initialize_loggers()

    histfile = os.path.join(CACHEDIR, "history")
    history = textio.TextIO(histfile, sort=False)
    argparser = parser.Parser(history)
    args = argparser.args
    url = args.url
    pages = args.pages
    parse_pages = files.PageNumbers(url)
    kwargs = rpc_kwargs()

    history.append_json_array(("url", url))

    try:
        print("Enumerating objects...")

        scraper = web.ScrapeWeb(CACHEDIR)
        pages = pages if pages else parse_pages.get_page_number()

        scraper.process_request(url)

        scraper.parse_magnets()

        names = scraper.names
        fuzzy_find = initialize_index(names)
        start, stop = intervals(pages)

        for i in range(start, stop):
            if parse_pages.ispage:
                url = parse_pages.select_page_number(i)

            scraper.process_request(url)

            scraper.parse_magnets()

            # match the above lists against the scraped files
            fuzzy_find.iterate(names)

            # initialize downloads for unmatched files
            # announce files added to the client
            # do not print report - too much text for multiple scrapes
            # the report can be viewed by running the report argument
            unmatched = fuzzy_find.get_matches("unowned")

            start_transmission(scraper.obj, unmatched, **kwargs)
    except (KeyboardInterrupt, EOFError):
        print("\u001b[0;31;40mProcess Terminated\u001b[0;0m")
