"""
categorpy.src.textio
====================

Write and read app data.
"""
import configparser
import datetime
import json
import logging
import logging.handlers
import os
import pathlib
import sys

from pygments import highlight

# noinspection PyUnresolvedReferences
from pygments.formatters import Terminal256Formatter  # pylint: disable=E0611

# noinspection PyUnresolvedReferences
from pygments.lexers import YamlLexer  # pylint: disable=E0611

from . import locate, log


class TextIO:
    """Read-write processes relevant to this package.

    :param path:    Path to read from or to write to.
    :key method:    Method to manipulate strings when writing from a
                    list. The method can be any function, or a string if
                    it is a builtin function belonging to the str class.
    :key args:      A tuple of args for the method key.
    :key sort:      Default is True: call False if a list we are writing
                    should not be sorted.
    """

    logger = log.get_logger()
    errlogger = log.get_logger("error")

    def __init__(self, path, _object=None, **kwargs):
        self.path = path
        self.ispath = os.path.isfile(path)
        self.output = ""
        self.object = _object if _object else {}
        self.method = kwargs.get("method", None)
        self.args = kwargs.get("args", ())

    def _output(self, content):
        self.output = f"{content}\n"

    def read_to_list(self):
        """Read from a file and return it's content as a list.

        :return: The file's content split into a list.
        """
        try:
            with open(self.path) as file:
                content = file.read().splitlines()
            return content
        except FileNotFoundError as err:
            self.errlogger.debug(str(err))
            return []

    def _execute(self, obj):
        if self.method:
            try:
                return getattr(obj, self.method)(*self.args)
            except TypeError:
                try:
                    function = self.method.rsplit(". ", 1)[1]
                    return getattr(self.method, function)(obj)
                except AttributeError as err:
                    self.errlogger.debug(str(err))
        return obj

    def _compile_string(self, content):
        self._output("\n".join(f"{self._execute(c)}" for c in content))

    def _write_file(self, mode):
        with open(self.path, mode) as file:
            file.write(self.output)

    def _mode(self, mode):
        if mode == "a":
            mode, self.ispath = (
                ("a", self.ispath) if self.ispath else ("w", True)
            )
        elif mode == "w":
            self.ispath = True
        return mode

    def append(self, content):
        """Append an entry to a file.

        :param content: The string to append to a file.
        """
        self.output = content
        self._write_file(self._mode("a"))

    def write(self, content):
        """Write content to a file, replacing all previous content that
        might have been there.

        :param content: The list to write into the file.
        """
        self.output = content
        self._write_file(self._mode("w"))

    def read(self):
        """Read from a file and return a single string, formatted with
        newlines.
        """
        content = self.read_to_list()
        self._compile_string(content)

    def read_bytes(self):
        """Read from a binary and return the content as bytes."""
        with open(self.path, "rb") as file:
            self.output = file.read()

    def read_json(self):
        """Read from a dictionary and return the content as a dictionary
        object.
        """
        try:
            with open(self.path) as file:
                self.object = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as err:
            self.errlogger.debug(str(err))

    def append_json_array(self, *args):
        """Write a tuple argument into a nested dictionary and write to
        a json file with the first index being the key and the second
        the value.

        :param args: A key value pair passed as a tuple.
        """
        self.read_json()
        for arg in args:
            try:
                self.object[arg[0]].append(arg[1])
            except KeyError as err:
                self.errlogger.debug(str(err))
                self.object[arg[0]] = [arg[1]]
        with open(self.path, "w") as file:
            file.write(json.dumps(self.object, indent=4))


def make_logger(logdir, name, debug=False):
    """Instantiate the global logging object containing several
    combined characteristics
    Create logging dir if one doesn't exist already
    Ensure all loggers contain the format "/$logdir/$logname"
    Ensure all loggers either display just the message or
    date-time, loglevel, message
    Ensure all loggers are configured to handle rotating logs
    Do not print logs to stdout or stderr
    """
    logfile = os.path.join(logdir, f"{name}.log")
    logger = logging.getLogger(name)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    filehandler = logging.handlers.WatchedFileHandler(logfile)

    filehandler.setFormatter(formatter)

    loglevel = logging.DEBUG if debug else logging.INFO

    logger.setLevel(loglevel)

    logger.addHandler(filehandler)


def pygment_print(string):
    """Print with ``pygments``. Read the string entered in method.
    Configure syntax highlighting for either shell or ini files and
    processes.

    :param string: What is to be printed.
    """
    print(
        highlight(string, YamlLexer(), Terminal256Formatter(style="monokai"))
    )


def record_hist(history, url):
    """Add url search history to history cache file. Increment id from
    the last search. Add timestamp.

    :param history: History object instantiated from
                    ``categorpy.TextIO``.
    :param url:     Url search or retrieved from prior history
                    - depending on whether an argument was passed to the
                    commandline.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    try:
        _id = history.object["history"][-1]["id"] + 1
    except KeyError:
        _id = 0

    history.append_json_array(
        ("history", {"id": _id, "timestamp": timestamp, "url": url})
    )


def initialize_paths_file(paths):
    """Make default file if it doesn't exist and read the file for paths
    that the user wants to scan for existing files to filter out of
    download. Default path to scan is the user's home directory.

    :return: List of paths to scan for files.
    """
    while True:
        pathio = TextIO(paths)
        if not pathio.read_to_list():
            pathio.write(str(pathlib.Path.home()))
            continue
        return pathio.read_to_list()


class Config:
    """Config for the module ``config.ini`` file located in the
    ``user_config_dir``.
    """

    def __init__(self):
        self.config_path = os.path.join(
            locate.APP.user_config_dir, "config.ini"
        )
        self.settings_path = os.path.join(
            locate.APP.client_dir, "settings.json"
        )
        self.object = configparser.ConfigParser()
        self._default_settings = {
            "DEFAULT": {"transmission": locate.APP.client_dir}
        }

    def _write_new(self):
        with open(self.config_path, "w") as file:
            self.object.write(file)

    def initialize_default(self):
        """Write a new ``config.ini`` file with default settings."""
        self.object.read_dict(self._default_settings)
        self._write_new()

    def initialize_existing(self):
        """Load an existing ``config.ini`` object into buffer as a
        dictionary object.
        """
        self.object.read(self.config_path)


def client_settings():
    """Attempt to read the settings.json file belonging to
    ``transmission_daemon`` and return it as a dictionary object parsed
    with the ``json`` module.
    """
    config = Config()
    if os.path.isfile(config.config_path):
        config.initialize_existing()
    else:
        config.initialize_default()
    try:
        settingsio = TextIO(config.settings_path)
        settingsio.read_json()
        return {
            "address": settingsio.object["rpc-bind-address"],
            "host": settingsio.object["rpc-host-whitelist"],
            "port": settingsio.object["rpc-port"],
            "username": settingsio.object["rpc-username"],
            "password": settingsio.object["rpc-password"],
            "path": os.path.join(settingsio.object["rpc-url"], "rpc"),
            "logger": log.get_logger("transmission"),
        }
    except FileNotFoundError as err:
        errlogger = log.get_logger("error")
        errlogger.exception(str(err))
        print(
            "\u001b[0;31;40mFatal error\u001b[0;0m"
            "`transmission-daemon' settings could not be found\n"
            "please check logs for more information",
            file=sys.stderr,
        )
        sys.exit(1)
