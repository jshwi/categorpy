"""
categorpy.src.find
==================

Find, match and reject.
"""
import logging
import re


class Normalize:
    """Format strings to a uniform syntax

    :param string: String to manipulate and use
    """

    def __init__(self, string):
        self.string = string

    def normalize_whitespace(self):
        """Convert all instances of dots and underscores to separate
        words as whitespace

        :return: Human readable sentence separated by whitespace
        """
        self.string = self.string.replace("_", " ")
        self.string = self.string.replace(".", " ")

    def normalize_non_alpha_numeric(self):
        """Remove such characters as pluses and minuses etc. and replace
        with whitespace
        """
        self.string = re.sub(r"([^\s\w]|_)+", " ", self.string)

    def set_lowercase(self):
        """Remove all case variances"""
        self.string = self.string.casefold()

    def deduplicate_whitespace(self):
        """If several characters have been replaced with whitespace then
        multiple spaces in the sentence can throw off a comparison
        search

        Make sure multiple whitespace occurrences are replaced with a
        single space
        """
        self.string = " ".join(self.string.split())

    def normalize(self):
        """Run all the regexes and string manipulations to normalize a
        string
        """
        self.set_lowercase()
        self.normalize_whitespace()
        self.normalize_non_alpha_numeric()
        self.deduplicate_whitespace()


class Ratio:
    """Work out the ratio of matching words to pass the cutoff"""

    exclude = ["and"]

    def __init__(self):
        self.debug_logger = logging.getLogger("debug")

    @staticmethod
    def count_obj(string1, string2):
        """Get ca key-value pair for a word and for the word itself and
        the number of occurrences of it within a string

        If there are too many reoccurrences of a word it can inflate the
        ratio for a similar word

        :param string1: The listed string - the download we are working
                        with
        :param string2: The string belonging to the hard drive that we
                        are testing for equality
        :return:        The dictionary object
        """
        return {
            w: string2.split().count(w)
            for w in string1.split()
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

    @staticmethod
    def work_percentage(string, match_len):
        """Get the final number of the length of the length of the
        string

        Get the length of the string containing it

        Work out the percentage that this one word occupies within the
        string

        :param string:      The string containing the words
        :param match_len:   The one word analyzed within the string
        :return:            An integer value for the percentage of the
                            string the word takes up
        """
        try:
            sum_ = sum(match_len)
            len_ = len("".join(string.split()))
            percent = sum_ / len_
            return percent
        except ZeroDivisionError:
            return 0

    def word_ratio(self, string1, string2):
        """Get the ratio of substrings within the two strings

        :param string1: String we are testing against (magnet)
        :param string2: The tester string (blacklist, owned)
        :return:        An integer for the percentage (or float - can't
                        remember right now)
        """
        word_count = self.count_obj(string1, string2)
        match_len = self.length_of_match(word_count)
        percent_match = self.work_percentage(string1, match_len)
        return 100 * percent_match

    def get_ratio(self, listed, test):
        """Get the final number of the ratio of matches between the
        two strings

        :param listed:  The magnet data
        :param test:    The blacklisted or owned file
        :return:        An integer (or float?) value for the ratio
        """
        normalize_listed = Normalize(listed)
        normalize_test = Normalize(test)

        normalize_listed.normalize()

        normalize_test.normalize()

        ratio = self.word_ratio(normalize_listed.string, normalize_test.string)

        self.debug_logger.debug("%s: %s", listed, ratio)

        return ratio


class Find(Ratio):
    """Find files by words not fuzziness

    :param blacklisted: List of blacklisted files
    :param owned:       List of owned files
    :param cutoff:      Percentage threshold for equality
    """

    def __init__(self, blacklisted, owned, cutoff=70):
        super().__init__()
        self.types = {
            "blacklisted": {"files": blacklisted, "matches": []},
            "owned": {"files": owned, "matches": []},
            "unowned": {"files": [], "matches": []},
            "rejected": {"files": [], "matches": []},
        }
        self.cutoff = cutoff
        self.info_logger = logging.getLogger("info")

    def get_matches(self, type_):
        """Get the dictionary matches from the instantiated object

        :param type_:   The key for the value to retrieve
        :return:        The list of matches for the type
        """
        return self.types[type_]["matches"]

    def match(self, listed, test):
        """Boolean for match or no match

        :param listed:  The string were filtering against
        :param test:    The owned or blacklisted object we are testing
                        against
        :return:        True or False
        """
        ratio = self.get_ratio(listed, test)
        return ratio > self.cutoff

    def log_found(self, decoded):
        """Log to logfile that a torrent valid for download has been
        found

        Ad the item to the matches value in the dictionary object

        :param decoded: The decoded magnet data
        """
        self.types["unowned"]["matches"].append(decoded)
        self.info_logger.info("[FOUND] %s", decoded)

    def log_rejected(self, key, decoded, file):
        """Log that an owned or blacklisted file has been found

        Add this to it's corresponding type in the ``self.types``
        dictionary

        Add this to the sub-total ``rejected`` key for analysis

        :param key:     The key that the rejected magnet belongs to i.e
                        was it blacklisted or is it already owned?
        :param decoded: The decoded magnet link data
        :param file:    The file we are testing the decoded magnet link
                        against
        """
        self.types[key]["matches"].append(file)
        self.types["rejected"]["matches"].append(file)
        self.info_logger.info("[%s] %s", key.upper(), decoded)

    def iterate_owned(self, decoded):
        """Loop through the owned files against the magnet link files

        :param decoded: The decoded magnet data
        :return:
        """
        for key, val in self.types.items():
            for file in val["files"]:
                if self.match(decoded, file):
                    self.log_rejected(key, decoded, file)
                    return
        self.log_found(decoded)

    def display_tally(self):
        """Display a live tally of where the process is for the user"""
        found = len(self.types["unowned"]["matches"])
        rejected = len(self.types["rejected"]["matches"])
        print(f"found: {found}    rejected: {rejected}", end="\r", flush=True)

    def iterate(self, magnets):
        """Iterate through the owned, blacklisted and magnet files and
        display what is happening to the user

        Log occurrences to info logfile

        Catch stacktrace from ValueError if there is nothing to retrieve
        and simply inform the user that nothing was found

        :param magnets: The scraped torrent data
        """
        self.info_logger.info("Finding wanted torrents")
        try:
            for magnet in magnets:
                self.iterate_owned(magnet)
                self.display_tally()
        except ValueError:
            print("Search returned no results...")
