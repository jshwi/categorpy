"""
settings
========

Interactive with the ``transmission-daemon`` ``setting.json`` file
"""
import configparser
import json
import os
import sys

from . import log, locate


class Config:
    """Config for the module ``config.ini`` file located in the
    ``user_config_dir``
    """

    def __init__(self):
        self.user_config_dir = locate.APPDIRS.user_config_dir
        self.config_file = os.path.join(self.user_config_dir, "config.ini")
        self.user_config_dirname = os.path.dirname(self.user_config_dir)
        self.client_dir = os.path.join(
            self.user_config_dirname, "transmission-daemon"
        )
        self.settings_file = os.path.join(self.client_dir, "settings.json")
        self.ini = configparser.ConfigParser()
        self._initialize_config()

    def read_existing(self):
        """Load an existing ``config.ini`` object into buffer as a
        dictionary object
        """
        self.ini.read(self.config_file)

    def write_new(self):
        """Write a new ``config.ini`` file with default settings"""
        default_settings = {"DEFAULT": {"transmission": self.client_dir}}
        self.ini.read_dict(default_settings)
        with open(self.config_file, "w") as file:
            self.ini.write(file)

    def _initialize_config(self):
        """Read from an existing config or initialize a config file with
        default values if one doesn't already exist
        """
        if not os.path.isfile(self.config_file):
            self.write_new()
        self.read_existing()

    def read_json(self):
        """Read the ``transmission-daemon`` ``settings.json`` file into
        buffer as a dictionary object

        :return:            Dictionary object containing all the
                            ``transmission-daemon`` settings
        """
        with open(self.settings_file) as file:
            return json.load(file)


def client_settings():
    """Attempt to read the settings.json file belonging to
    ``transmission_daemon`` and return it as a dictionary object parsed
    with the ``json`` module
    """
    config = Config()
    logger = log.get_logger("transmission")
    try:
        kwargs = config.read_json()
        return {
            "host": kwargs["rpc-host-whitelist"],
            "port": kwargs["rpc-port"],
            "username": kwargs["rpc-username"],
            "password": kwargs["rpc-password"],
            "path": os.path.join(kwargs["rpc-url"], "rpc"),
            "logger": logger,
        }
    except FileNotFoundError:
        errlogger = log.get_logger("error")
        errlogger.exception(
            "`transmission-daemon' settings could not be found"
        )
        print(
            "\u001b[0;31;40mFatal error\u001b[0;0m\n"
            "`transmission-daemon' settings could not be found\n"
            "please check logs for more information",
            file=sys.stderr,
        )
        sys.exit(1)
