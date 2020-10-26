"""
tests.helpers
=============

Helper constants, functions and classes for tests
"""
import sys
from unittest import mock

import keyring.backend

import categorpy


class KeyringTest(keyring.backend.KeyringBackend):
    """A test keyring which always outputs same password"""

    priority = 1

    def __init__(self):
        self.password = None

    def set_password(
        self, servicename, username, password
    ):  # pylint: disable=W0221,W0613
        # testing set password
        self.password = password

    def get_password(
        self, servicename, username
    ):  # pylint: disable=W0221,W0613
        return self.password

    def delete_password(
        self, servicename, username
    ):  # pylint: disable=W0221,W0613
        # testing delete password
        self.password = None


def mock_main(*args):
    """A function to mock the main() function executed in __main__

    Mock sys.argv to replace any realtime commandline input with strings
    to test with pytest

    :param args: commandline arguments to pass to ``main``
    """
    argv = [__file__, *args]
    with mock.patch.object(sys, "argv", argv):
        categorpy.main.main()


def password_mocker(password, stdin):
    """Mock stdin for ``getpass``

    :param password:    List of password attempts
    :param stdin:       List of input attempts
    """
    output = []

    def mock_password(stdout):
        output.append(stdout)
        return password.pop(0)

    def mock_input(stdout):
        output.append(stdout)
        return stdin.pop(0)

    categorpy.main.client.auth.getpass.getpass = mock_password

    categorpy.main.client.input = mock_input


def null_side_effect(*_, **__):
    """Stop use of ``transmission_rpc.Client``"""
    return None
