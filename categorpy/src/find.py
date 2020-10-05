"""
categorpy.src.find
==================

Find, match and reject.
"""
import fnmatch
import re

from . import files, locate, log, normalize, textio


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
        self.int = round(100 * percent_match)

    def get_ratio(self):
        """Get the final number of the ratio of matches between the
        two strings

        :return: An integer value for the ratio
        """
        self.string1.normalize()
        self.string2.normalize()
        self.word_ratio()


def match_ratio(magnet, exclude, cutoff):
    """Boolean for match or no match

    :param magnet:      The string were filtering against
    :param exclude:    The owned or blacklisted object we are testing
                        against
    :param cutoff:
    :return:            True or False
    """
    logger = log.get_logger()
    ratio = Ratio(magnet, exclude)
    ratio.get_ratio()
    match = ratio.int > cutoff
    if match:
        logger.debug("[RATIO] {%s: %s}", magnet, ratio.int)
    return match


def match_globs(magnet, exclude):
    """Append files matching globs which are supported in certain
    data-files

    :param magnet:  Match the globs against the magnet-files to
                    filter out the unwanted magnets
    :param exclude:
    """
    logger = log.get_logger()
    try:
        exclude = exclude.replace(" ", "_")
        match = fnmatch.fnmatch(magnet.casefold(), exclude.casefold())
        if match:
            logger.debug("[PATTERN] {%s: %s}", magnet, exclude)
        return match
    except re.error as err:
        logger.warning(msg=str(err), exc_info=True)
        return False


class Find:
    """Find files by words not fuzziness

    :param cutoff: Percentage threshold for equality
    """

    def __init__(self, cutoff=70, globs=None, **kwargs):
        self.types = kwargs
        self.found = []
        self.rejected = []
        self.cutoff = cutoff
        self.glob = globs if globs else []

    def _get_match(self, key, magnet, exclude):
        if key in self.glob:
            return match_globs(magnet, exclude)
        return match_ratio(magnet, exclude, self.cutoff)

    def iterate_owned(self, magnet):
        """Loop through the owned files against the magnet link files

        :param magnet: The decoded magnet data
        """
        for key in self.types:
            for exclude in self.types[key]:
                if self._get_match(key, magnet, exclude):
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
        try:
            self.found.clear()
            self.rejected.clear()
            for magnet in magnets:
                logger = log.get_logger()
                status = self.iterate_owned(magnet)
                status = status.upper()
                logger.info("[%s] %s", status, magnet)
                self.display_tally()
        except ValueError:
            print("Search returned no results...")


def analyze_files():
    """Loop over page numbers entered for url

    Instantiate fuzzy find class with all the lists to match against
    print report and cache report files and get list of unmatched files
    that can be downloaded

    load up ``transmission``

    :return: Instantiated ``find.Find`` object
    """
    blacklistio = textio.TextIO(locate.APPFILES.blacklist)
    blacklist = blacklistio.read_to_list()

    torrents = files.Torrents()

    print("Scanning local torrents")
    torrents.parse_torrents()

    paths_list = textio.initialize_paths_file(locate.APPFILES.paths)

    idx = log.log_time("Indexing", files.index_path, args=(paths_list,))

    keys = list(torrents.obj.keys())

    return Find(
        downloading=keys,
        blacklisted=blacklist,
        owned=idx,
        globs=["blacklisted"],
    )
