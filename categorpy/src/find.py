"""
categorpy.src.find
==================

Find, match and reject.
"""
import fnmatch
import logging
import re

from . import normalize

LOGGER = logging.getLogger("categorpy")


class Ratio:
    """Work out the ratio of matching words to pass the cutoff"""

    exclude = ["and"]

    def __init__(self, string1, string2):
        self.string1 = normalize.File(string1)
        self.string2 = normalize.File(string2)
        self.int = 0

    def count_obj(self):
        """Get ca key-value pair for a word and for the word itself and
        the number of occurrences of it within a string

        If there are too many reoccurrences of a word it can inflate the
        ratio for a similar word

        :return: The dictionary object
        """
        return {
            w: self.string2.string.split().count(w)
            for w in self.string1.string.split()
            if w not in Ratio.exclude
        }

    @staticmethod
    def length_of_match(word_count):
        """Get the length (in letters) of a word and its single or
        multiple occurrences

        :param word_count:  Dictionary object containing the word as the
                            key and the occurrences of it as the value
        :return:            An integer value for the length of the word
                            and its variable occurrences in terms of the
                            the number of letters only
        """
        return [len(k * v) for k, v in word_count.items()]

    def work_percentage(self, match_len):
        """Get the final number of the length of the length of the
        string

        Get the length of the string containing it

        Work out the percentage that this one word occupies within the
        string

        :param match_len:   The one word analyzed within the string
        :return:            An integer value for the percentage of the
                            string the word takes up
        """
        try:
            sum_ = sum(match_len)
            len_ = len("".join(self.string1.string.split()))
            percent = sum_ / len_
            return percent
        except ZeroDivisionError:
            return 0

    def word_ratio(self):
        """Get the ratio of substrings within the two strings

        :return:    An integer for the percentage (or float - can't
                    remember right now)
        """
        word_count = self.count_obj()
        match_len = self.length_of_match(word_count)
        percent_match = self.work_percentage(match_len)
        self.int = 100 * percent_match

    def get_ratio(self):
        """Get the final number of the ratio of matches between the
        two strings

        :return: An integer (or float?) value for the ratio
        """
        self.string1.normalize()

        self.string2.normalize()

        self.word_ratio()

        LOGGER.debug("%s: %s", self.string1.string, self.int)


class Find:
    """Find files by words not fuzziness

    :param cutoff:      Percentage threshold for equality
    """

    def __init__(self, cutoff=70, globs=None, **kwargs):
        self.types = kwargs
        self.found = []
        self.rejected = []
        self.cutoff = cutoff
        self.glob = globs if globs else []

    def ratio(self, listed, test):
        """Boolean for match or no match

        :param listed:  The string were filtering against
        :param test:    The owned or blacklisted object we are testing
                        against
        :return:        True or False
        """
        ratio = Ratio(listed, test)
        ratio.get_ratio()
        return ratio.int > self.cutoff

    @staticmethod
    def globs(magnet, file):
        """Append files matching globs which are supported in certain
        data-files

        :param magnet:  Match the globs against the magnet-files to
                        filter out the unwanted magnets
        :param file:
        """
        try:
            file = file.replace(" ", "_")
            return fnmatch.fnmatch(magnet.casefold(), file.casefold())
        except re.error as err:
            LOGGER.warning("re.error - %s\n%s\n", err, file)
            return False

    def iterate_owned(self, magnet):
        """Loop through the owned files against the magnet link files

        :param magnet: The decoded magnet data
        """
        for key in self.types:
            for file in self.types[key]:
                match = self.globs if key in self.glob else self.ratio
                if match(magnet, file):
                    self.rejected.append(magnet)
                    return key
        self.found.append(magnet)
        return "found"

    def display_tally(self):
        """Display a live tally of where the process is for the user"""
        print(
            f"found: {len(self.found)}    rejected: {len(self.rejected)}",
            end="\r",
            flush=True,
        )

    def iterate(self, magnets):
        """Iterate through the owned, blacklisted and magnet files and
        display what is happening to the user

        Log occurrences to info logfile

        Catch stacktrace from ValueError if there is nothing to retrieve
        and simply inform the user that nothing was found

        :param magnets: The scraped torrent data
        """
        LOGGER.info("Finding torrents")
        try:
            for magnet in magnets:
                status = self.iterate_owned(magnet)
                status = status.upper()
                LOGGER.info("[%s] %s", status, magnet)
                self.display_tally()
        except ValueError:
            print("Search returned no results...")
