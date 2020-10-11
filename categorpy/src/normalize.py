"""
categorpy.src.normalize
=======================

Use regular expressions and string manipulation methods to turn hard to
read content into human readable content which will make it easier to
draw comparisons between strings.
"""
import re
from urllib import parse

from . import log


class File:
    """Format strings to a uniform syntax

    :param string: String to manipulate and use.
    """

    def __init__(self, string):
        self.string = string

    def normalize_whitespace(self):
        """Convert all instances of dots and underscores to separate
        words as whitespace.

        :return: Human readable sentence separated by whitespace.
        """
        self.string = self.string.replace("_", " ")
        self.string = self.string.replace(".", " ")

    def normalize_non_alpha_numeric(self):
        """Remove such characters as pluses and minuses etc. and replace
        with whitespace.
        """
        self.string = re.sub(r"([^\s\w]|_)+", " ", self.string)

    def set_lowercase(self):
        """Remove all case variances."""
        self.string = self.string.casefold()

    def deduplicate_whitespace(self):
        """If several characters have been replaced with whitespace then
        multiple spaces in the sentence can throw off a comparison
        search.

        Make sure multiple whitespace occurrences are replaced with a
        single space.
        """
        self.string = " ".join(self.string.split())

    def normalize(self):
        """Run all the regexes and string manipulations to normalize a
        string.
        """
        self.set_lowercase()
        self.normalize_whitespace()
        self.normalize_non_alpha_numeric()
        self.deduplicate_whitespace()


class Magnet:
    """Get the name of a magnet-link file

    :param magnet: Magnet file's contents parsed with ``bencode.py``.
    """

    def __init__(self, magnet):
        self.magnet = magnet

    def remove_equals(self):
        """Separate the words by whitespace instead of an equals
        sign.
        """
        self.magnet = "".join(self.magnet.split("=")[2:])

    def remove_last_delim(self):
        """Remove the last delimiter from the magnet's contents."""
        self.magnet = "".join(self.magnet.split("&tr")[:1])

    def remove_underscore(self):
        """Separate the words by whitespace instead of an underscore."""
        self.magnet = self.magnet.strip("_")

    def remove_quotes(self):
        """Remove the quotes from a magnet links content."""
        self.magnet = parse.unquote(self.magnet)

    def remove_tuple(self):
        """Remove the tuple from a magnet-link with regular
        expressions.
        """
        removelist = "()"
        self.magnet = re.sub(
            " +", "_", re.sub(r"[^\w" + removelist + "]", " ", self.magnet)
        )

    def normalize(self):
        """Combine all methods to manipulate and change the magnet
        content.
        """
        self.remove_equals()
        self.remove_last_delim()
        self.remove_underscore()
        self.remove_quotes()
        self.remove_tuple()


class Decoder:
    """Analyze a dictionary object recursively to decode all nested
    values containing ``bytes``.
    """

    @staticmethod
    def _is_bytes(item):
        """Determine whether a a value is a ``bytes`` object.

        :param item:    The value to test.
        :return:        True: is ``bytes``, False: is not.
        """
        return isinstance(item, bytes)

    @classmethod
    def decode_key(cls, key):
        """If ``key`` is type ``bytes`` return decoded ``str`` object,
        if not then nothing needs to be done - return the original
        object.

        :param key: Dictionary key.
        :return:    Return a decoded ``str``.
        """
        if cls._is_bytes(key):
            return key.decode()
        return key

    @classmethod
    def decode_val(cls, val):
        """A value belonging to a key-value pair can be any object so
        if the object is not bytes begin the iteration again to iterate
        and decode over any ``list``, ``dict`` or ``bytes`` object
        further down.

        :param val: ``str``, ``list``, ``dict`` or ``bytes``.
        :return:    ``list``, ``dict`` or ``str``.
        """
        if cls._is_bytes(val):
            return val.decode()
        return cls.decode(val)

    @classmethod
    def decode_dict(cls, _object):
        """Pass a ``dict`` object to recursively analyze for values
        which are the type ``bytes``.

        :param _object: The ``dict`` object.
        :return:        Analyzed and altered ``dict`` object.
        """
        for key in list(_object):
            val = _object.pop(key)
            key = cls.decode_key(key)
            _object[key] = cls.decode_val(val)
        return _object

    @classmethod
    def decode_list(cls, _object):
        """Pass a ``list`` object to recursively analyze for values
        which are the type ``bytes``.

        :param _object: The ``list`` object.
        :return:        Analyzed and altered ``list`` object.
        """
        for count, val in enumerate(_object):
            val = _object[count]
            _object[count] = cls.decode_val(val)
        return _object

    @classmethod
    def decode(cls, _object):
        """Recursively go through a ``list`` or ``dict`` object -
        ignoring the ``UnicodeDecodeError`` that may occur.

        :param _object: The ``list`` or ``dict`` object.
        :return:        Analyzed and altered ``list`` or ``dict``
                        object.
        """
        try:
            if isinstance(_object, dict):
                return cls.decode_dict(_object)
            if isinstance(_object, list):
                return cls.decode_list(_object)
        except UnicodeDecodeError as err:
            errlogger = log.get_logger("error")
            errlogger.exception(str(err))
        return _object
