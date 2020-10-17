"""
conftest

Custom fixtures for tests
"""
import os
from unittest import mock

import pytest

import categorpy
from tests import helpers

APPNAME = "categorpy"


@pytest.fixture(name="make_loggers")
def fixture_make_loggers(tmpdir):
    """Set up a mock instance of categorpy.main to test auth"""
    mock.patch.object(os.path, "expanduser", tmpdir)
    categorpy.main.log.make_logger(name="error", debug=True)
    categorpy.main.log.make_logger(name=APPNAME, debug=True)


@pytest.fixture(name="nocolorcapsys")
def fixture_nocolorcapsys(capsys):
    """Instantiate capsys with the regex method

    :param capsys: ``pytest`` fixture
    :return:        Instantiated ``NoColorCapsys`` object
    """
    return helpers.NoColorCapsys(capsys)


@pytest.fixture(name="mock_appfiles")
def fixture_mock_appfiles(tmpdir):
    """Instantiate and return ``MockAppFiles`` as a fixture

    :param tmpdir:  ``pytest`` fixture
    :return:        ``MockAppDirs``
    """
    return helpers.MockAppFiles(tmpdir)
