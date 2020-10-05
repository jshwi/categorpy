"""
categorpy.src.auth
==================

Securely handle user authentication.
"""
import getpass

import keyring
import keyring.errors

from . import log


class Keyring:
    """Authorization object consisting of methods utilizing ``getpass``
    and ``keyring``

    :param servicename: Name for the user's keyring
    :param username:    User's username
    """

    def __init__(self, servicename, username):
        self.servicename = servicename
        self.username = username
        self.headless = False
        self.password = None
        self._get_password()
        self.saved = self.password is not None
        self.entered = 0

    def _get_password(self):
        try:
            self.password = keyring.get_password(
                self.servicename, self.username
            )
        except keyring.errors.KeyringLocked as err:
            logger = log.get_logger()
            logger.exception(str(err))
            self.headless = True

    def add_password(self):
        """Prompt user for their password and save to instance
        variable
        """
        if self.headless:
            print(
                "Headless server detected:\n"
                "please enter your password as one cannot be saved or loaded\n"
            )
        self.password = getpass.getpass("Password: ")
        self.entered += 1

    def save_password(self):
        """Add the user's password to their keyring

        Switch instance variable ``saved`` from False to True to
        indicate the user has already been prompted to save their
        password
        """
        keyring.set_password(self.servicename, self.username, self.password)
        self.saved = True
