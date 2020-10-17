"""
tests._test
===========

Tests for ``categorpy``
"""
import sys
from unittest import mock

import pytest

import categorpy
from tests import helpers, expected


@pytest.mark.usefixtures("make_loggers")
@mock.patch("categorpy.main.client.transmission_rpc.Client")
def test_auth_all_ok(mock_transmission, mock_appfiles):
    """Test that the auth loop works in ``categorpy.main``

    :param mock_transmission: Mock ``transmission-rpc`` object
    """
    categorpy.main.locate.APP = mock_appfiles
    categorpy.main.client.auth.keyring.set_keyring(helpers.KeyringTest())
    helpers.password_mocker(password=["correct"], stdin=["y"])
    mock_transmission.side_effect = [
        categorpy.main.client.transmission_rpc.error.TransmissionError,
        helpers.null_side_effect,
        helpers.null_side_effect,
    ]
    keyring = categorpy.main.client.auth.Keyring("transmission", "admin")
    categorpy.main.client.get_client(keyring, settings={})


@pytest.mark.usefixtures("make_loggers")
@mock.patch("categorpy.main.client.transmission_rpc.Client")
def test_auth_3_failed_attempts(
    mock_transmission, nocolorcapsys, mock_appfiles
):
    """Test that the program exits and displays the correct error
    message if 3 incorrect password attempts are made

    :param mock_transmission:   Mock ``transmission-rpc`` object
    :param nocolorcapsys:       Capsys without ANSI escape codes
    """
    categorpy.main.locate.APP = mock_appfiles
    categorpy.main.client.auth.keyring.set_keyring(helpers.KeyringTest())
    helpers.password_mocker(password=["wrong", "wrong", "wrong"], stdin=[])
    mock_transmission.side_effect = [
        categorpy.main.client.transmission_rpc.error.TransmissionError,
        categorpy.main.client.transmission_rpc.error.TransmissionError,
        categorpy.main.client.transmission_rpc.error.TransmissionError,
        categorpy.main.client.transmission_rpc.error.TransmissionError,
    ]
    keyring = categorpy.main.client.auth.Keyring("transmission", "admin")
    with pytest.raises(SystemExit):
        categorpy.main.client.get_client(keyring, settings={})
    stderr = nocolorcapsys.stderr()
    assert stderr == expected.AUTH_FAIL


# noinspection DuplicatedCode
@pytest.mark.usefixtures("make_loggers")
@mock.patch("categorpy.main.client.transmission_rpc.Client")
@mock.patch.object(
    categorpy.main.client.web.Scraper,
    "process_request",
    helpers.null_side_effect,
)
@mock.patch.object(
    categorpy.main.client.web.Scraper, "scrape", helpers.null_side_effect
)
@mock.patch.object(
    categorpy.main.client.transmission_rpc.Client,
    "add_torrent",
    helpers.null_side_effect,
)
@mock.patch.object(categorpy.main, "parse_url", helpers.url_side_effect)
@mock.patch.object(
    categorpy.main.textio, "client_settings", helpers.transmission_settings
)
def test_password_persistence(mock_transmission):
    """Test that the program exits and displays the correct error
    message if 3 incorrect password attempts are made

    :param mock_transmission: Mock ``transmission-rpc`` object
    """
    logger = categorpy.main.log.get_logger()
    categorpy.main.client.auth.keyring.set_keyring(helpers.KeyringTest())
    helpers.password_mocker(password=["correct"], stdin=["y"])
    mock_transmission.side_effect = [
        categorpy.main.client.transmission_rpc.error.TransmissionError,
        categorpy.main.client.transmission_rpc.Client,
        categorpy.main.client.transmission_rpc.Client,
        categorpy.main.client.transmission_rpc.Client,
        categorpy.main.client.transmission_rpc.Client,
        categorpy.main.client.transmission_rpc.Client,
    ]
    sys.argv = sys.argv[4:]
    logger.debug(sys.argv)
    argparser = categorpy.main.Parser()
    args = argparser.args
    args.url = categorpy.main.parse_url(argparser)
    args.pages = "1-5"
    find = categorpy.main.find.Find(
        blacklist=[], downloading=[], owned=[], globs=["blacklisted"]
    )
    categorpy.main.client.transmission(args, find)
