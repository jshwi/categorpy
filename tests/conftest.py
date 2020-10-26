"""
conftest

Custom fixtures for tests
"""
import os
import pathlib
import re
from unittest import mock

import pytest

import categorpy


APPNAME = "categorpy"


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


def prep_path(dirname, basename):
    """Put together a path to a directory, create the directory and
    then return it to be used

    :param dirname:     Path dirname
    :param basename:    Directory to create
    :return:            Path to the directory
    """
    path = os.path.join(dirname, basename)
    pathobj = pathlib.Path(path)
    # pathobj.mkdir(parents=True, exist_ok=True)
    return str(pathobj)


@pytest.fixture(name="configdir")
def fixture_configdir(tmpdir):
    """Create config directory and use it

    :param tmpdir: ``pytest`` temporary directory fixture
    :return:        Path to the .config dir
    """
    return prep_path(tmpdir, ".config")


@pytest.fixture(name="cachedir")
def fixture_cachedir(tmpdir):
    """Create cache directory and use it

    :param tmpdir: ``pytest`` temporary directory fixture
    :return:        Path to the .cache dir
    """
    return prep_path(tmpdir, ".cache")


@pytest.fixture(name="categorpy_logs")
def fixture_categorpy_logs(categorpy_cache):
    """Create log directory and use it

    :param categorpy_cache: Path to the .cache dir
    :return:                Path to the log dir
    """
    return prep_path(categorpy_cache, "log")


@pytest.fixture(name="transmission_config")
def fixture_transmission_config(configdir):
    """Create ``transmission-daemon`` config dir and use it

    :param configdir:   Path to the .config dir
    :return:            Path to the ``transmission-daemon`` .config dir
    """
    return prep_path(configdir, "transmission-daemon")


@pytest.fixture(name="categorpy_config")
def fixture_categorpy_config(configdir):
    """Create categorpy config dir and use it

    :param configdir:   Path to the .config dir
    :return:            Path to the categorpy .config dir
    """
    return prep_path(configdir, "categorpy")


@pytest.fixture(name="categorpy_cache")
def fixture_categorpy_cache(cachedir):
    """Create categorpy cache dir and use it

    :param cachedir:    Path to the .cache dir
    :return:            Path to the categorpy .cache dir
    """
    return prep_path(cachedir, "categorpy")


@pytest.fixture(name="transmission_settings")
def fixture_transmission_settings(transmission_config):
    """Write a ``transmission-daemon`` settings.json file to ``tmpdir``

    :param transmission_config: Path to the ``tmpdir``
                                ``transmission-daemon`` config dir
    :return:                    Path to the ``tmpdir``
                                ``transmission-daemon`` setting.json
                                file
    """
    obj = {
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
    transmission_settings = os.path.join(transmission_config, "settings.json")
    settings = categorpy.main.textio.JsonIO(file=transmission_settings)
    settings.write(obj)
    return transmission_settings


@mock.patch("categorpy.locate.APP")
def mock_app(mock_appdirs, categorpy_logs, categorpy_cache, categorpy_config):
    """Replace the values in the instantiated
    ``categorpy.locate.AppFiles`` with mock paths stemming from
    ``tmpdir``

    :param mock_appdirs:        Mock ``categorpy.locate.APP`` object
    :param categorpy_cache:     <tmpdir>/.cache/
    :param categorpy_logs:      <tmpdir>/.cache/log/
    :param categorpy_config:    <tmpdir>/.config/
    """
    mock_appdirs.user_cache_dir = categorpy_cache
    mock_appdirs.user_config_dir = categorpy_config
    mock_appdirs.user_log_dir = categorpy_logs


@pytest.fixture(name="make_loggers")
def fixture_make_loggers(tmpdir):
    """Set up a mock instance of categorpy.main to test auth

    :param tmpdir: ``pytest`` fixture
    """
    mock.patch.object(os.path, "expanduser", tmpdir)
    mock.patch("categorpy.locate.APP")
    categorpy.main.log.make_logger(name="error", debug=True)
    categorpy.main.log.make_logger(name=APPNAME, debug=True)


@pytest.fixture(name="nocolorcapsys")
def fixture_nocolorcapsys(capsys):
    """Instantiate capsys with the regex method

    :param capsys: ``pytest`` fixture
    :return:        Instantiated ``NoColorCapsys`` object
    """
    return NoColorCapsys(capsys)
