"""
categorpy.src.client
====================

All things ``transmission-rpc``.
"""
import requests
import transmission_rpc

from . import auth, config, exception, locate, log, pages, textio, web


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


def instantiate_client():
    """Attempt to instantiate the ``transmission_rpc.Client`` class or
    log an error and explain the nature of the fault to the user before
    exiting with a non-zero exit code

    :return:        Instantiated ``transmission_rpc.Client`` class
    """
    kwargs = config.client_settings()
    keyring = auth.Keyring(locate.APPNAME, kwargs.get("username", ""))
    kwargs["password"] = keyring.password
    password_protect = False
    logger = log.get_logger()
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
            with log.StreamLogger(name="transmission", level="DEBUG"):
                client = transmission_rpc.Client(**kwargs)

            # if the process has made it this far then if
            # password_protected is False break and return client
            # if `password_protected' is True user has the option to
            # save the password to the OS specific password store so
            # they do not need to use a password with this program again
            # and afterwards will proceed to break and return client
            if not keyring.saved and not keyring.headless and password_protect:
                choice = input("would you like to save this password?\n")
                if choice.casefold() == "y":
                    keyring.save_password()
                    print("password saved")
            return client

        except transmission_rpc.error.TransmissionError as err:
            password_protect = True

            try:
                # if more than 3 incorrect password attempts have been made
                # the process will give up and exit
                if keyring.entered >= 1:
                    prior_auth(keyring.entered)

                # if the process has reached this block than the client has
                # attempted to be instantiated but has raised a
                # transmission_rpc.error.TransmissionError due to either
                # not having entered a password yet or not entered a
                # correct password previously
                logger.debug(str(err), exc_info=True)
                keyring.add_password()
            except (KeyboardInterrupt, EOFError):
                exception.terminate_proc()

            kwargs["password"] = keyring.password

            # continue on to attempt to instantiate the client again
            continue

        # will be raised from a series of errors not directly invoked
        # by this process such as those from the requests library or
        # urllib etc
        except (requests.exceptions.ConnectionError, ValueError) as err:
            exception.exit_fatal(err)


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


def transmission(args, find):
    """Take the url, selected page numbers, iterated file matches and
    ``transmission-daemon`` settings.json object and iterate over the
    page-range and download torrents

    :param args:    Instantiated ``argparse.Namespace`` object for
                    commandline arguments
    :param find:    Instantiated ``find.Find`` object containing
                    found non-matching or non-blacklisted torrents
    """
    logger = log.get_logger()
    parse_pages = pages.Pages(args.url, args.pages)
    scraper = web.ScrapeWeb()

    for i in range(parse_pages.start, parse_pages.stop):
        if parse_pages.ispage:
            args.url = parse_pages.select_page_number(i)

        print(f"page: {i}")

        scraper.process_request(args.url)

        scraper.scrape_magnets()

        scraper.parse_magnets()

        scraper_keys = scraper.get_scraped_keys()

        find.iterate(scraper_keys)

        info = start_transmission(scraper.object, find.found)

        logger.info("\n%s", info)

        textio.pygment_print(info)
