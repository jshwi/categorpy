"""
categorpy.src.auth
==================

Securely handle user authentication.
"""
import getpass
import sys

import keyring
import keyring.errors

from . import log


class Keyring:
    """Authorization object consisting of methods utilizing ``getpass``
    and ``keyring``.

    :param servicename: Name for the user's keyring.
    :param username:    User's username.
    """

    def __init__(self, servicename, username):
        self.servicename = servicename
        self.username = username
        self.password = None
        self.headless = False
        self.saved = False
        self.entered = 0
        self.get_password()

    def get_password(self):
        """Get stored password from system keyring. If one cannot be
        retrieved then the keyring has not been unlocked - this will
        usually be done automatically on a Linux system when running the
        GUI. It is most likely then that this session is being run
        through SSH. Notify the user that they will need to enter the
        password, even if one is already stored.
        """
        try:
            self.password = keyring.get_password(
                self.servicename, self.username
            )
        except keyring.errors.KeyringLocked as err:
            errlogger = log.get_logger("error")
            errlogger.debug(str(err), exc_info=True)
            self.headless = True
        self.saved = self.password is not None

    def add_password(self):
        """Prompt user for their password and save to instance
        variable.
        """
        if self.headless:
            print(
                "Headless server detected:\n"
                "please enter your password as one cannot be saved or loaded\n"
            )
        self.password = getpass.getpass("Password: ")
        self.entered += 1

    def save_password(self):
        """Add the user's password to their keyring. Switch instance
        variable ``saved`` from False to True to indicate the user has
        already been prompted to save their password.
        """
        keyring.set_password(self.servicename, self.username, self.password)
        self.saved = True


def prior_auth(entered):
    """Start tally of incorrect login attempts and log these as info to
    the ``info.log`` file. On the 3rd attempt log this to the
    ``error.log`` file. Announce that the ``transmission-daemon``
    settings.json file may need updating if user does not know their
    password.

    :param entered: Number of times an incorrect password has been
                    entered.
    """
    logger = log.get_logger()
    errlogger = log.get_logger("error")
    tally = f"{entered} incorrect password attempts"
    logger.info(tally)
    if entered == 3:
        print(
            "\u001b[0;31;40mToo many incorrect password attempts\u001b[0;0m\n"
            "please update your password in `transmission-daemon' "
            "settings.json and try again",
            file=sys.stderr,
        )
        errlogger.error(tally)
        sys.exit(1)
    print("\nincorrect password: please try again")
