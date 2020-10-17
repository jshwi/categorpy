"""
tests.helpers
=============

Helper constants, functions and classes for tests
"""
import os
import pathlib
import re
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


class MockAppFiles:  # pylint: disable=R0902,R0903
    """Mock ``APP`` for tests

    :param tmpdir: Pass temporary dir fixture to class as function
    """

    def __init__(self, tmpdir):
        self.appname = "categorpy"
        self.user_config_dir = os.path.join(tmpdir, ".config")
        self.user_cache_dir = os.path.join(tmpdir, ".cache")
        self.user_log_dir = os.path.join(
            self.user_cache_dir, "categorpy", "log"
        )
        self.config = os.path.join(self.user_config_dir, "config.ini")
        self.user_config_dirname = os.path.dirname(self.user_config_dir)
        self.client_dir = os.path.join(
            self.user_config_dirname, "transmission-daemon"
        )
        self.torrents = os.path.join(self.client_dir, "torrents")
        self.paths = os.path.join(self.user_config_dir, "paths")
        self.settings = os.path.join(self.client_dir, "settings.json")
        self.histfile = os.path.join(self.user_cache_dir, "history")
        self._make_dirs()

    @staticmethod
    def prep_path(directory):
        """create dir similar to mkdir -p /path/to/dir to create parent
        dirs too
        """
        pathobj = pathlib.Path(directory)
        pathobj.mkdir(parents=True, exist_ok=True)

    def _make_dirs(self):
        """Make app dirs"""
        dirs = [
            self.user_config_dir,
            self.user_cache_dir,
            self.user_log_dir,
            self.user_config_dirname,
            self.client_dir,
            self.torrents,
        ]
        for _dir in dirs:
            self.prep_path(_dir)


class NoColorCapsys:
    """Capsys but with a regex to remove ANSI escape codes

    Class is preferable for this as we can instantiate the instance
    as a fixture that also contains the same attributes as capsys

    We can make sure that the class is instantiated without executing
    capsys immediately thus losing control of what stdout and stderr
    we are to capture

    :param capsys: ``pytest's`` builtin fixture to capture system output
    """

    def __init__(self, capsys):
        self.capsys = capsys

    @staticmethod
    def regex(out):
        """Replace ANSI color codes with empty strings i.e. remove all
        escape codes

        Prefer to test colored output this way as colored strings can
        be tricky and the effort in testing their validity really isn't
        worth it. Also hard to read expected strings when they contain
        the codes.

        :param out: String to strip of ANSI escape codes
        :return:    Same string but without ANSI codes
        """
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", out)

    def readouterr(self):
        """Call as capsys ``readouterr`` but regex the strings for
        escape codes at the same time

        :return:    A tuple (just like the capsys) containing stdout in
                    the first index and stderr in the second
        """
        readouterr = self.capsys.readouterr()
        return tuple([self.regex(r) for r in readouterr])

    def _readouterr_index(self, idx):
        readouterr = self.readouterr()
        return readouterr[idx]

    def stdout(self):
        """Call this to return the stdout without referencing the tuple
        indices
        """
        return self._readouterr_index(0)

    def stderr(self):
        """Call this to return the stderr without referencing the tuple
        indices
        """
        return self._readouterr_index(1)


def transmission_settings():
    """Write a ``transmission-daemon`` settings.json file to
    ``tmpdir``
    """
    return {
        "alt-speed-down": 50,
        "alt-speed-enabled": False,
        "alt-speed-time-begin": 540,
        "alt-speed-time-day": 127,
        "alt-speed-time-enabled": False,
        "alt-speed-time-end": 1020,
        "alt-speed-up": 50,
        "bind-address-ipv4": "0.0.0.0",
        "bind-address-ipv6": "::",
        "blocklist-enabled": False,
        "blocklist-url": "http://www.example.com/blocklist",
        "cache-size-mb": 4,
        "dht-enabled": True,
        "download-dir": "/var/lib/transmission-daemon/downloads",
        "download-limit": 100,
        "download-limit-enabled": 0,
        "download-queue-enabled": True,
        "download-queue-size": 5,
        "encryption": 1,
        "idle-seeding-limit": 30,
        "idle-seeding-limit-enabled": False,
        "incomplete-dir": "/var/lib/transmission-daemon/Downloads",
        "incomplete-dir-enabled": False,
        "lpd-enabled": False,
        "max-peers-global": 200,
        "message-level": 1,
        "peer-congestion-algorithm": "",
        "peer-id-ttl-hours": 6,
        "peer-limit-global": 200,
        "peer-limit-per-torrent": 50,
        "peer-port": 51413,
        "peer-port-random-high": 65535,
        "peer-port-random-low": 49152,
        "peer-port-random-on-start": False,
        "peer-socket-tos": "default",
        "pex-enabled": True,
        "port-forwarding-enabled": False,
        "preallocation": 1,
        "prefetch-enabled": True,
        "queue-stalled-enabled": True,
        "queue-stalled-minutes": 30,
        "ratio-limit": 2,
        "ratio-limit-enabled": False,
        "rename-partial-files": True,
        "rpc-authentication-required": True,
        "rpc-bind-address": "0.0.0.0",
        "rpc-enabled": True,
        "rpc-host-whitelist": "",
        "rpc-host-whitelist-enabled": True,
        "rpc-password": "{7e406b195b71a2d88910662494fa0f2b808f43b5jlI1E5/j",
        "rpc-port": 9091,
        "rpc-url": "/transmission/",
        "rpc-username": "transmission",
        "rpc-whitelist": "127.0.0.1",
        "rpc-whitelist-enabled": True,
        "scrape-paused-torrents-enabled": True,
        "script-torrent-done-enabled": False,
        "script-torrent-done-filename": "",
        "seed-queue-enabled": False,
        "seed-queue-size": 10,
        "speed-limit-down": 100,
        "speed-limit-down-enabled": False,
        "speed-limit-up": 100,
        "speed-limit-up-enabled": False,
        "start-added-torrents": True,
        "trash-original-torrent-files": False,
        "umask": 18,
        "upload-limit": 100,
        "upload-limit-enabled": 0,
        "upload-slots-per-torrent": 14,
        "utp-enabled": True,
    }


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


def url_side_effect(*_, **__):
    """Stop use of ``transmission_rpc.Client``"""
    return "https://google.com"
