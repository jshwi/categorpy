"""
categorpy.src.textio
====================

Write and read app data.
"""
import contextlib
import json
import logging
import logging.handlers
import os

from pygments import highlight

# noinspection PyUnresolvedReferences
from pygments.formatters import Terminal256Formatter  # pylint: disable=E0611

# noinspection PyUnresolvedReferences
from pygments.lexers import YamlLexer  # pylint: disable=E0611


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

    def write_list(self, content):
        """Write content to a file, replacing all previous content that
        might have been there

        :param content: The list to write into the file
        """
        content = self._passive_dedupe(content)
        self._compile_string(content)
        self._write_file(self._mode("w"))

    def append(self, content):
        """Append an entry to a file

        :param content: The string to append to a file
        """
        self.output = content
        self._write_file(self._mode("a"))

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
        if not os.path.isfile(self.path):
            with open(self.path, "w") as _:
                # python version of shell's `touch`
                pass


def make_logger(loglevel, logdir):
    """Instantiate the global logging object containing several
    combined characteristics
    Create logging dir if one doesn't exist already
    Ensure all loggers contain the format "/$logdir/$logname"
    Ensure all loggers either display just the message or
    date-time, loglevel, message
    Ensure all loggers are configured to handle rotating logs
    Do not print logs to stdout or stderr
    """
    logfile = os.path.join(logdir, f"{loglevel}.log")
    logger = logging.getLogger(loglevel)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    filehandler = logging.handlers.WatchedFileHandler(logfile)

    filehandler.setFormatter(formatter)

    logger.setLevel(logging.INFO)

    logger.addHandler(filehandler)


class StreamLogger:
    """Run as a context class using ``with`` to capture output stream"""

    def __init__(self, name="debug", level="DEBUG"):
        self.logger = logging.getLogger(name)
        self.name = self.logger.name
        self.level = getattr(logging, level)
        self._redirector = contextlib.redirect_stdout(self)

    def write(self, msg):
        """Will be called when used as a contextlib action

        :param msg: The message to log - stdout stream
        """
        if msg and not msg.isspace():
            self.logger.log(self.level, msg)

    def flush(self):
        """For when we are capturing stdout or stderr"""
        pass  # pylint: disable=W0107

    def __enter__(self):
        self._redirector.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # let contextlib do any exception handling here
        self._redirector.__exit__(exc_type, exc_val, exc_tb)


def pygment_print(string):
    """Print with ``pygments``

    Read the string entered in method

    Configure syntax highlighting for either shell or ini files and
    processes

    :param string:  What is to be printed
    """
    print(
        highlight(string, YamlLexer(), Terminal256Formatter(style="monokai"))
    )
