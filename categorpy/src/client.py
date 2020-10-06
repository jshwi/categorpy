"""
categorpy.src.client
====================

All things ``transmission-rpc``.
"""
import sys

import requests
import transmission_rpc

from . import auth, locate, log, textio, torrents


def get_client(keyring, settings):
    """Attempt to instantiate the ``transmission_rpc.Client`` class or
    log an error and explain the nature of the fault to the user before
    exiting with a non-zero exit code.

    :param keyring:     Instantiated ``Keyring`` object to store and
                        retrieve passwords.
    :param settings:    Dictionary object containing
                        ``transmission-daemon`` settings from
                        settings.json.
    :return:            Instantiated ``transmission_rpc.Client`` class.
    """
    password_protect = False
    errlogger = log.get_logger("error")
    while True:
        try:
            # if `keyring.password' is not None on first try a password
            # has been saved to the keyring from a prior run
            # if `keyring.password' is None on first loop but on any
            # more than one then a password has been entered during this
            # run - if the password is incorrect then a
            # transmission.error.TransmissionError will be raised and
            # the loop will continue below
            # if `keyring.password' is None then no password has been
            # saved during this run or a prior run and
            # `transmission-daemon' is protected with auth then a
            # transmission_rpc.error.TransmissionError will be raised
            # and the loop will continue below
            # none of this is relevant if "rpc-authentication-required"
            # is False and unless any http errors etc. are raised
            # transmission_rpc.Client will be returned from this
            # function
            with log.StreamLogger("transmission"):
                client = transmission_rpc.Client(**settings)

            # if the process has made it this far then if
            # password_protected is False break and return client
            # if `password_protected' is True user has the option to
            # save the password to the OS specific password store so
            # they do not need to use a password with this program again
            # and afterwards will proceed to break and return client
            if not keyring.saved and not keyring.headless and password_protect:
                choice = input("save password? [y/N]\n")
                if choice.casefold() == "y":
                    keyring.save_password()
                    print("password saved")

            return client

        except transmission_rpc.error.TransmissionError as err:
            errlogger.debug(str(err), exc_info=True)
            password_protect = True

            # if more than 3 incorrect password attempts have been made
            # the process will give up and exit
            if keyring.entered >= 1:
                auth.prior_auth(keyring.entered)

            # if the process has reached this block than the client has
            # attempted to be instantiated but has raised a
            # transmission_rpc.error.TransmissionError due to either
            # not having entered a password yet or not entered a
            # correct password previously
            keyring.add_password()
            settings["password"] = keyring.password

        # will be raised from a series of errors not directly invoked
        # by this process such as those from the requests library or
        # urllib etc
        except (requests.exceptions.ConnectionError, ValueError) as err:
            errlogger.exception(str(err))
            print(
                "\u001b[0;31;40mFatal error\u001b[0;0m{body}\n"
                "the process could not continue\n"
                "`transmission-daemon' may not be configured correctly\n"
                "please check logs for more information",
                file=sys.stderr,
            )
            sys.exit(1)


def load_client(magnets, unmatched, keyring, settings):
    """Compare magnet files parsed from bencode text into plaintext
    against existing files on the user's system. If the
    ``matched_magnets`` list has been populated announce to the user the
    files which have begun downloading. Announce to user if no new files
    can be downloaded from the scrape.

    :param magnets:         List of magnet contents (not paths).
    :param unmatched:       List of torrents that have been scraped and
                            are not owned (in plaintext).
    :param keyring:         Instantiated ``Keyring`` object to store and
                            retrieve passwords.
    :param settings:        Dictionary object containing
                            ``transmission-daemon`` settings from
                            settings.json.
    :return:                Info summary for what has happened whilst
                            running ``transmission-daemon``.
    """
    unowned_magnets = [v for k, v in magnets.items() if k in unmatched]
    if unowned_magnets:
        client = get_client(keyring, settings)
        for magnet in unowned_magnets:
            client.add_torrent(magnet)
        return (
            "The Following Unmatched Torrents Have Just Been Added:\n"
            + "- "
            + "\n- ".join(unmatched)
        )
    return "*** There's Nothing to Add ***\n"


def transmission(args, find):
    """Take the URL, selected page numbers, iterated file matches and
    ``transmission-daemon`` settings.json object and iterate over the
    page-range and download torrents.

    :param args:    Instantiated ``argparse.Namespace`` object for
                    commandline arguments.
    :param find:    Instantiated ``find.Find`` object containing
                    found non-matching or non-blacklisted torrents.
    """
    logger = log.get_logger()
    pages = torrents.Pages(args.url, args.pages)
    scraper = torrents.Scrape()
    settings = textio.client_settings()
    keyring = auth.Keyring(locate.APP.appname, settings.get("username", ""))
    for page in range(pages.start, pages.stop):
        if pages.ispage:
            args.url = pages.page_number(page)
        print(f"Pg. {page}")
        scraper.process_request(args.url)
        scraper.scrape_magnets()
        scraper.parse_magnets()
        magnets = scraper.get_names()
        find.iterate(magnets)
        info = load_client(scraper.object, find.found, keyring, settings)
        logger.info("\n%s", info)
        textio.pygment_print(info)
