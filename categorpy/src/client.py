"""
categorpy.src.client
====================

All things ``transmission-rpc``.
"""
import getpass

import transmission_rpc

from . import log, exception, textio, pages, web


def prior_auth(entered):
    """Start tally of incorrect login attempts and log these as info to
    the ``info.log`` file

    On the 3rd attempt log this to the ``error.log`` file

    Announce that the ``transmission-daemon`` settings.json file may
    need updating if user does not know their password

    :param entered: Number of times an incorrect password has been
                    entered
    """
    logger = log.get_logger()
    tally = f"{entered} incorrect password attempts"
    logger.info(tally)
    if entered == 3:
        exception.exit_max_auth(tally)
    print("\nincorrect password: please try again")


def instantiate_client(**kwargs):
    """Attempt to instantiate the ``transmission_rpc.Client`` class or
    log an error and explain the nature of the fault to the user before
    exiting with a non-zero exit code

    :param kwargs:  Key-value settings read from the
                    ``transmission-daemon`` settings.json file
    :return:        Instantiated ``transmission_rpc.Client`` class
    """
    entered = 0
    while True:
        # noinspection PyBroadException
        try:
            with log.StreamLogger("info"):
                return transmission_rpc.Client(**kwargs)
        except transmission_rpc.error.TransmissionError:
            if entered:
                prior_auth(entered)
            kwargs["password"] = getpass.getpass("\nPassword: ")
            entered += 1
            continue
        except Exception:  # pylint: disable=W0703
            exception.terminate_proc()


def run_client(unowned_magnets, unmatched):
    """Load the magnet links into the rpc client

    :param unowned_magnets: Magnets not owned by user so good to load
    :param unmatched:       Unmatched human readable names of magnets
    :return:                Info regarding what torrent were loaded into
                            client
    """
    client = instantiate_client()
    for magnet in unowned_magnets:
        client.add_torrent(magnet)
    newfiles = "- " + "\n- ".join(unmatched)
    return (
        f"The Following Unmatched Torrents Have Just Been Added:\n"
        f"{newfiles}\n"
    )


def start_transmission(magnets, unmatched):
    """Compare magnet files parsed from bencode text into plaintext
    against existing files on the user's system

    If the `matched_magnets` list has been populated announce to the
    user the files which have begun downloading

    Announce to user if no new files can be downloaded from the scrape

    :param magnets:         List of magnet contents (not paths)
    :param unmatched:       List of torrents that have been scraped and
                            are not owned (in plaintext)
    :return:                Info summary for what has happened whilst
                            running ``transmission-daemon``
    """
    unowned_magnets = [v for k, v in magnets.items() if k in unmatched]
    if unowned_magnets:
        return run_client(unowned_magnets, unmatched)
    return "*** There's Nothing to Add ***\n"


def transmission(argparser, find):
    """Take the url, selected page numbers, iterated file matches and
    ``transmission-daemon`` settings.json object and iterate over the
    page-range and download torrents

    :param argparser:   Instantiated ``argparse.ArgumentParser`` object
                        for commandline arguments
    :param find:        Instantiated ``find.Find`` object containing
                        found non-matching or non-blacklisted torrents
    """
    logger = log.get_logger()
    parse_pages = pages.Pages(argparser.args.url, argparser.args.pages)
    scraper = web.ScrapeWeb()

    for i in range(parse_pages.start, parse_pages.stop):
        if parse_pages.ispage:
            argparser.args.url = parse_pages.select_page_number(i)

        print(f"page: {i}")

        find.clear()

        scraper.process_request(argparser.args.url)

        scraper.scrape_magnets()

        scraper.parse_magnets()

        scraper_keys = scraper.get_scraped_keys()

        find.iterate(scraper_keys)

        info = start_transmission(scraper.object, find.found)

        logger.info("\n%s", info)

        textio.pygment_print(info)
