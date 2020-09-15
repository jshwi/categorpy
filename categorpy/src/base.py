"""
base
====

Functions and classes shared by all other modules
"""
import argparse
import datetime
import json
import logging
import os

import appdirs
import object_colors

APPNAME = "categorpy"

TIME = datetime.datetime.now().strftime("T%H:%M:%S")
DATE = datetime.date.today().strftime("%Y-%m-%d")
SUFFIX = f"{DATE}{TIME}"
CACHEDIR = appdirs.user_cache_dir(APPNAME)
LOGDIR = os.path.join(CACHEDIR, "log")
REPORTDIR = os.path.join(CACHEDIR, "report")
DISPLAYDIR = os.path.join(CACHEDIR, "display")
HISTORY = os.path.join(CACHEDIR, "history")
HTTP = os.path.join(CACHEDIR, "http")
MAGNET = os.path.join(CACHEDIR, "magnets")
DATADIR = appdirs.user_data_dir(APPNAME)
BLACKLIST = os.path.join(DATADIR, "blacklist")
PACK = os.path.join(DATADIR, "pack")
DATE = datetime.date.today().strftime("%Y%m%d")
TIME = datetime.datetime.now().strftime("%H:%M:%S")
COLOR = object_colors.Color()

COLOR.populate_colors()


class Walk:
    """
    Walk through the directory passed with the root parameter

    Inherit this class to pass a method and args for files we wish to
    ignore

    :param root:        The root directory which the class will walk
    :param method:      The method that the class inheriting this class
                        will pass to super
    :param args:        Directories that the inheriting class wants to
                        ignore
    """

    def __init__(self, root, method, *args):
        super().__init__()
        self._root = root
        self._method = method
        self._ignore = args

    def walk_files(self, root, files):
        """Call the method within the file iteration

        :param root:    Top level of directory structure
        :param files:   List of files within directory structure
        """
        for file in files:
            fullpath = os.path.join(root, file)
            self._method(fullpath)

    def walk_dirs(self):
        """Iterate through walk if the root directory exists

        - Skip directories in list parameter and create fullpath
          with root and files
        - forget about the directories returned by walk
        - Once files are determined perform the required actions
        """
        if os.path.isdir(self._root):
            for root, _, files in os.walk(self._root, followlinks=True):
                if self._ignore and root in self._ignore:
                    continue
                self.walk_files(root, files)


class IndexDir(Walk):
    """Index the directory provided into a list of absolute paths

    :param root:        The root directory which the class will walk
    :param args:        Directories that the inheriting class wants to
                        ignore
    """

    def __init__(self, root, *args):
        self.pathlist = []
        super().__init__(root, self._get_list, *args)
        self._populate_list()

    def _populate_list(self):
        self.walk_dirs()

    def _get_list(self, file):
        self.pathlist.append(file)
        self.pathlist = sorted(self.pathlist)


class TextIO:
    """Read-write processes relevant to this package

    :param path:    Path to read from or to write to
    :key method:    Method to manipulate strings when writing from a
                    list. The method can be any function, or a string if
                    it is a builtin function belonging to the str class
    :key args:      A tuple of args for the method key
    :key sort:      Default is True: call False if a list we are writing
                    should not be sorted
    """

    def __init__(self, path, **kwargs):
        self.path = path
        self.ispath = os.path.isfile(path)
        self.output = ""
        self.object = {}
        self.method = kwargs.get("method", None)
        self.args = kwargs.get("args", ())
        self.sort = kwargs.get("sort", True)

    def _passive_dedupe(self, content):
        return sorted(list(set(content))) if self.sort else content

    def _output(self, content):
        self.output = f"{content}\n"

    def read_to_list(self):
        """Read from a file and return it's content as a list

        :return: The file's content split into a list
        """
        with open(self.path) as file:
            content = file.read().splitlines()
        return content

    def _active_dedupe(self):
        if self.ispath and self.sort:
            content = self.read_to_list()
            self._compile_string(content)
            self.write_list(content)

    def _execute(self, obj):
        if self.method:
            try:
                return getattr(obj, self.method)(*self.args)
            except TypeError:
                try:
                    function = self.method.rsplit(". ", 1)
                    return getattr(self.method, function)(obj)
                except AttributeError:
                    pass
        return obj

    # noinspection PyArgumentList
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
        """Append an entry to a file

        :param content: The string to append to a file
        """
        self._active_dedupe()
        self._output(content)
        self._write_file(self._mode("a"))

    def write_list(self, content):
        """Write content to a file, replacing all previous content that
        might have been there

        :param content: The list to write into the file
        """
        content = self._passive_dedupe(content)
        self._compile_string(content)
        self._write_file(self._mode("w"))

    def write(self, content):
        """Write content to a file, replacing all previous content that
        might have been there

        :param content: The list to write into the file
        """
        self.output = content
        self._write_file(self._mode("w"))

    def read(self):
        """Read from a file and return a single string, formatted with
        newlines
        """
        content = self.read_to_list()
        self._compile_string(content)

    def read_bytes(self):
        """Read from a binary and return the content as bytes"""
        with open(self.path, "rb") as file:
            self.output = file.read()

    def read_json(self):
        """Read from a dictionary and return the content as a dictionary
        object
        """
        try:
            with open(self.path) as file:
                self.object = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def append_json_array(self, *args):
        """Write a tuple argument into a nested dictionary and write to
        a json file with the first index being the key and the second
        the value

        :param args: A key value pair passed as a tuple

        .. code-block:: console

            (key, value)
        ..
        """
        self.read_json()
        for arg in args:
            try:
                self.object[arg[0]].append(arg[1])
            except KeyError:
                self.object[arg[0]] = [arg[1]]
        with open(self.path, "w") as file:
            file.write(json.dumps(self.object, indent=4))

    def touch(self):
        """Create an empty file"""
        with open(self.path, "w") as _:
            # python version of shell's `touch`
            pass


def parse_file(path):
    """Read a file into this session and attempt to resolve any
    non-critical errors

    If no content can be retrieved return an empty list

    :param path:    the file path to read from
    :return:        A list of the file's content
    """
    textio = TextIO(path)
    if os.path.isfile(path):
        return textio.read_to_list()
    parent = os.path.basename(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    textio.touch()
    return []


def get_index(path, *ignore):
    """Get a list of a directories files all as absolute paths

    Pass files to be ignored

    :param path:    The path to get the files from
    :param ignore:  Files that should not be added to the list
    :return:        A list of absolute paths
    """
    index_files = IndexDir(path, *ignore)
    return index_files.pathlist


def base_parser(module_name, *_, max_help_position=42):
    module = COLOR.cyan.get(f"ctgpy {module_name}")
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(
        prog=module,
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog, max_help_position=max_help_position
        ),
    )
    return parser


def logger(message, **kwargs):
    loglevel = kwargs.get("loglevel", "info")
    if loglevel == "warning":
        logfunc = logging.warning
    else:
        logfunc = logging.info
    suffix = f"{DATE}.log"
    filename = os.path.join(LOGDIR, f"{loglevel}-{suffix}")
    logging.basicConfig(
        filename=filename,
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    logfunc(message)
