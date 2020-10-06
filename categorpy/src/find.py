"""
categorpy.src.find
==================

Find, match and reject.
"""
import fnmatch
import os
import pathlib
import re

from . import normalize, locate, log, torrents, textio


class Ratio:
    """Work out the ratio of matching words to pass the cutoff.

    :param string1: The main string to test against.
    :param string2: The string to match the ratio against ``string1``.
    """

    exclude = ["and"]

    def __init__(self, string1, string2):
        self.string1 = normalize.File(string1)
        self.string2 = normalize.File(string2)
        self.int = 0

    def count_obj(self):
        """Get ca key-value pair for a word and for the word itself and
        the number of occurrences of it within a string. If there are
        too many reoccurrences of a word it can inflate the ratio for a
        similar word.

        :return: The dictionary object.
        """
        return {
            w: self.string2.string.split().count(w)
            for w in self.string1.string.split()
            if w not in Ratio.exclude
        }

    @staticmethod
    def length_of_match(word_count):
        """Get the length (in letters) of a word and its single or
        multiple occurrences.

        :param word_count:  Dictionary object containing the word as the
                            key and the occurrences of it as the value.
        :return:            An integer value for the length of the word
                            and its variable occurrences in terms of the
                            the number of letters only.
        """
        return [len(k * v) for k, v in word_count.items()]

    def work_percentage(self, match_len):
        """Get the final number of the length of the length of the
        string. Get the length of the string containing it. Work out the
        percentage that this one word occupies within the string.

        :param match_len:   The one word analyzed within the string.
        :return:            An integer value for the percentage of the
                            string the word takes up.
        """
        try:
            sum_ = sum(match_len)
            len_ = len("".join(self.string1.string.split()))
            percent = sum_ / len_
            return percent
        except ZeroDivisionError:
            return 0

    def word_ratio(self):
        """Get the ratio of substrings within the two strings.

        :return: An integer for the percentage.
        """
        word_count = self.count_obj()
        match_len = self.length_of_match(word_count)
        percent_match = self.work_percentage(match_len)
        self.int = round(100 * percent_match)

    def get_ratio(self):
        """Get the final number of the ratio of matches between the
        two strings.

        :return: An integer value for the ratio.
        """
        self.string1.normalize()
        self.string2.normalize()
        self.word_ratio()


class Find:
    """Find files by words or by globs - not fuzziness.

    :param cutoff: Percentage threshold for equality. If over 7 words
                    in 10 are the same (by default) then exclude file
                    from being loaded.
    :param globs:   List of ``types`` that will not be tested for word
                    similarity but for glob patterns.
    :param types:   Lists of files to test against found magnets for
                    equality.
    """

    logger = log.get_logger()
    errlogger = log.get_logger("error")

    def __init__(self, cutoff=70, globs=None, **types):
        self.cutoff = cutoff
        self.globs = globs if globs else []
        self.types = types
        self.found = []
        self.rejected = []

    def match_ratio(self, magnet, exclude):
        """Boolean for match or no match.

        :param magnet:  The string were filtering against.
        :param exclude: The owned or blacklisted object we are testing
                        against.
        :return:        Is the ratio above the cutoff? True or False.
        """
        ratio = Ratio(magnet, exclude)
        ratio.get_ratio()
        match = ratio.int > self.cutoff
        if match:
            self.logger.debug("[RATIO] {%s: %s}", magnet, ratio.int)
        return match

    @classmethod
    def match_globs(cls, magnet, exclude):
        """Append files matching globs which are supported in certain
        data-files.

        :param magnet:  Match the globs against the magnet-files to
                        filter out the unwanted magnets.
        :param exclude: String that we do not want to include when adding
                        torrents to ``transmission-rpc``.
        """
        try:
            exclude = exclude.replace(" ", "_")
            match = fnmatch.fnmatch(magnet.casefold(), exclude.casefold())
            if match:
                cls.logger.debug("[PATTERN] {%s: %s}", magnet, exclude)
            return match
        except re.error as err:
            cls.errlogger.debug(str(err), exc_info=True)
            return False

    def _is_match(self, key, magnet, exclude):
        # either match by ratio of matching words of match by glob
        # patterns
        if key in self.globs:
            return self.match_globs(magnet, exclude)
        return self.match_ratio(magnet, exclude)

    def iterate_owned(self, magnet):
        """Loop through the owned files against the magnet link files.

        :param magnet: The decoded magnet data.
        """
        for key in self.types:
            for exclude in self.types[key]:
                if self._is_match(key, magnet, exclude):
                    self.rejected.append(magnet)
                    return key
        self.found.append(magnet)
        return "found"

    def display_tally(self):
        """Display a live tally of where the process is for the user."""
        print(
            f"found: {len(self.found)}    rejected: {len(self.rejected)}",
            end="\r",
            flush=True,
        )

    def iterate(self, magnets):
        """Iterate through the owned, blacklisted and magnet files and
        display what is happening to the user. Log occurrences to info
        logfile. Catch stacktrace from ValueError if there is nothing to
        retrieve and simply inform the user that nothing was found.

        :param magnets: The scraped torrent data.
        """
        try:
            self.found.clear()
            self.rejected.clear()
            for magnet in magnets:
                status = self.iterate_owned(magnet)
                status = status.upper()
                self.logger.info("[%s] %s", status, magnet)
                self.display_tally()
        except ValueError as err:
            self.errlogger.debug(str(err), exc_info=True)
            print("Search returned no results...")


def instantiate_find(cutoff):
    """Loop over page numbers entered for URL. Instantiate ``Find``
    class with all the lists to match against. Load up ``transmission``.

    :param cutoff:  The amount of similar words that are allowed in.
                    By default the cutoff is 70 (%), as in anything
                    higher will mean a matching string.
    :return:        Instantiated ``find.Find`` object.
    """
    blacklistio = textio.TextIO(locate.APP.blacklist)
    blacklisted = blacklistio.read_to_list()
    decoder = torrents.Read()

    print("Scanning local torrents")

    decoder.parse_torrents()

    paths = textio.initialize_paths_file(locate.APP.paths)
    owned = log.log_time("Indexing", index_path, args=(paths,))
    downloading = decoder.get_decoded_names()

    return Find(
        cutoff=cutoff,
        globs=["blacklisted"],
        downloading=downloading,
        blacklisted=blacklisted,
        owned=owned,
    )


def index_path(paths):
    """get list of all system files with the wildcard glob pattern to
    ``pathlib.Path``.

    :param paths:   List of paths that the user has configured to
                    analyze for files.
    :return:        List of indexed file basenames (not their full
                    path).
    """
    files = []
    for path in paths:
        pathobj = pathlib.Path(path)
        files.extend(
            [
                os.path.basename(str(f))
                for f in pathobj.rglob("*")
                if os.path.isfile(str(f))
            ]
        )
    return files
