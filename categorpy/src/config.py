"""
settings
========

Interactive with the ``transmission-daemon`` ``setting.json`` file
"""
import configparser
import json
import os
import pathlib


class Config:
    """Config for the module ``config.ini`` file located in the
    ``user_config_dir``
    """

    def __init__(self, configdir):
        self.configdir = configdir
        self.configpath = os.path.join(configdir, "config.ini")
        self.path = pathlib.Path(configdir)
        self.user_config = os.path.dirname(configdir)
        self.client_dir = os.path.join(self.user_config, "transmission-daemon")
        self.ini = configparser.ConfigParser()
        self.make_config_dir()

    def make_config_dir(self):
        """Make a directory for the ``appname`` config file"""
        self.path.mkdir(parents=True, exist_ok=True)

    def read_existing(self):
        """Load an existing ``config.ini`` object into buffer as a
        dictionary object
        """
        self.ini.read(self.configpath)

    def write_new(self):
        """Write a new ``config.ini`` file with default settings"""
        default_settings = {"DEFAULT": {"transmission": self.client_dir}}
        self.ini.read_dict(default_settings)
        with open(self.configpath, "w") as file:
            self.ini.write(file)

    def initialize_config(self):
        """Read from an existing config or initialize a config file with
        default values if one doesn't already exist
        """
        if not os.path.isfile(self.configpath):
            self.write_new()
        self.read_existing()

    def read_json(self):
        """Read the ``transmission-daemon`` ``settings.json`` file into
        buffer as a dictionary object

        :return:            Dictionary object containing all the
                            ``transmission-daemon`` settings
        """
        client_dir = self.ini["DEFAULT"]["transmission"]
        settings = os.path.join(client_dir, "settings.json")
        with open(settings) as file:
            return json.load(file)
