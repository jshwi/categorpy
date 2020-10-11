"""
categorpy.src.textio
====================

Write and read app data.
"""
import configparser
import datetime
import json
import os
import pathlib
import sys

# noinspection PyPackageRequirements
import bencodepy
from pygments import highlight

# noinspection PyUnresolvedReferences
from pygments.formatters import Terminal256Formatter  # pylint: disable=E0611

# noinspection PyUnresolvedReferences
from pygments.lexers import YamlLexer  # pylint: disable=E0611

from . import locate, log, normalize


class ListIO:
    """Object to represent file in ``list`` form through the process
    while keeping the file in sync when changes are made to instance.

    :param file: File to read / write to.
    """

    def __init__(self, file):
        self.file = file
        self.array = []
        self.read()

    def _write_list(self):
        with open(self.file, mode="w") as file:
            for line in self.array:
                file.write(line)

    def clear(self):
        """Run this before ``self.write`` to start the file over."""
        self.array.clear()

    def read(self):
        """Read from file and add list items to ``self.array``."""
        if os.path.isfile(self.file):
            with open(self.file) as file:
                content = file.read()
            self.array.extend(content.splitlines())

    def write(self, *lines):
        """Write content to a file, replacing all previous content that
        might have been there. Appending to file is the default
        behaviour.

        :param lines: The list to write into the file.
        """
        self.array.extend(lines)
        self._write_list()


class JsonIO:
    """Object to represent file in ``json`` form through the process
    while keeping the file in sync when changes are made to instance.

    :param file: File to read / write to.
    """

    def __init__(self, file):
        self.file = file
        self.object = {}
        self.read()

    def _write_json(self):
        with open(self.file, mode="w") as file:
            file.write(json.dumps(self.object, indent=4))

    def clear(self):
        """Run this before ``self.write`` to start the file over."""
        self.object.clear()

    def read(self):
        """If the ``self.file`` path exists then read its content in the
        ``self.object`` instance attribute.
        """
        if os.path.isfile(self.file):
            try:
                with open(self.file) as file:
                    self.object.update(json.load(file))
            except json.JSONDecodeError as err:
                errlogger = log.get_logger("error")
                errlogger.debug(str(err))

    def write(self, _object):
        """Write ``dict`` object to file as ``json``.

        :param _object: The ``dict`` object.
        """
        self.object.update(_object)
        self._write_json()

    def append_array(self, **kwargs):
        """Write a tuple argument into a nested dictionary and write to
        a json file with the first index being the key and the second
        the value.

        :key array: Name of the array to add items to.
        :var value: string, object, array etc to append to array.
        """
        for key, val in kwargs.items():
            if key not in self.object:
                self.object[key] = []
            self.object[key].append(val)
        self._write_json()


class IniIO:
    """Object to represent file in ``ini`` form through the process
    while keeping the file in sync when changes are made to instance.

    :param file: File to read / write to.
    """

    def __init__(self, file):
        self.file = file
        self.object = configparser.ConfigParser()

    def _write_new(self):
        with open(self.file, "w") as file:
            self.object.write(file)

    def initialize_default(self, default):
        """Write a new ``config.ini`` file with default settings."""
        self.object.read_dict(default)
        self._write_new()

    def initialize_existing(self):
        """Load an existing ``config.ini`` object into buffer as a
        dictionary object.
        """
        self.object.read(self.file)


class BencodeIO:
    """Parse downloaded data for human readable categorisation."""

    errlogger = log.get_logger("error")

    def __init__(self, torrent_dir):
        self.torrent_dir = torrent_dir
        self.names = []

    def _get_torrent_paths(self, paths):
        """Get the torrent magnet-link files.

        :return: List of torrent magnet-links.
        """
        if os.path.isdir(self.torrent_dir):
            paths.extend(
                [
                    os.path.join(self.torrent_dir, t)
                    for t in os.listdir(self.torrent_dir)
                ]
            )
        return paths

    @classmethod
    def parse_bencode_object(cls, bencode):
        """take bencode content (not path) and convert it to human
        readable text.

        :param bencode: Bytes read from torrent file.
        """
        encoded = bencodepy.decode(bencode)
        obj = normalize.Decoder.decode(encoded)
        try:
            if "magnet-info" in obj and "display-name" in obj["magnet-info"]:
                result = obj["magnet-info"]["display-name"]
                return result.replace("+", " ")
        except bencodepy.exceptions.BencodeDecodeError as err:
            cls.errlogger.exception(str(err))
        return None

    def parse_torrents(self):
        """Call to get the readable content from the bencode and create
        a dictionary object of names and their corresponding magnets.
        """
        paths = self._get_torrent_paths(paths=[])
        for path in paths:
            # get the bencode bytes from their .torrent file
            with open(path, mode="rb") as file:
                bencode = file.read()

            # parse these bytes into human readable plaintext
            decoded = self.parse_bencode_object(bencode)
            if decoded:

                # update the torrent file object with the torrent file's
                # name as the key and it's path as the value
                self.names.append(decoded)


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

    def _hist_id(_history):
        try:
            return _history.object["history"][-1]["id"] + 1
        except KeyError:
            return 0

    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    _id = _hist_id(history)

    history.append_array(
        history={"id": _id, "timestamp": timestamp, "url": url}
    )


def initialize_paths_file(paths_file):
    """Make default file if it doesn't exist and read the file for paths
    that the user wants to scan for existing files to filter out of
    download. Default path to scan is the user's home directory.

    :return: List of paths to scan for files.
    """
    pathio = ListIO(paths_file)
    if not os.path.isfile(paths_file):
        home = str(pathlib.Path.home())
        pathio.write(home)
    return pathio.array


def client_settings():
    """Attempt to read the settings.json file belonging to
    ``transmission_daemon`` and return it as a dictionary object parsed
    with the ``json`` module.
    """
    config = IniIO(locate.APP.config)
    if os.path.isfile(locate.APP.config):
        config.initialize_existing()
    else:
        default = {"DEFAULT": {"transmission": locate.APP.client_dir}}
        config.initialize_default(default)
    try:
        settingsio = JsonIO(locate.APP.settings)
        return {
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
