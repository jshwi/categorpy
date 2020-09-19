"""
find
====

Find, match and reject
"""
import logging
import re


class Ratio:

    exclude = ["and"]

    def __init__(self):
        self.debug_logger = logging.getLogger("debug")

    @staticmethod
    def _normalize(strings):
        for count, string in enumerate(strings):
            replace = string.casefold().replace("_", " ").replace(".", " ")
            regex = re.sub(r"([^\s\w]|_)+", " ", replace)
            strings[count] = " ".join(regex.split())
        return strings

    @staticmethod
    def _work_percentage(string, match_len):
        try:
            sum_ = sum(match_len)
            len_ = len("".join(string.split()))
            percent = sum_ / len_
            return percent
        except ZeroDivisionError:
            return 0

    def word_ratio(self, string1, string2):
        word_count = {
            w: string2.split().count(w)
            for w in string1.split()
            if w not in Ratio.exclude
        }
        match_len = [len(k * v) for k, v in word_count.items()]
        percent_match = self._work_percentage(string1, match_len)
        return 100 * percent_match

    def get_ratio(self, listed, test):
        strings = self._normalize([listed, test])
        ratio = self.word_ratio(*strings)
        self.debug_logger.debug("%s: %s", listed, ratio)
        return ratio


class Find(Ratio):
    """Find files by words not fuzziness"""

    def __init__(self, **kwargs):
        super().__init__()
        self.types = {
            "blacklisted": {
                "files": kwargs.get("blacklisted", []),
                "matches": [],
            },
            "owned": {"files": kwargs.get("owned", []), "matches": []},
            "unowned": {"files": [], "matches": []},
            "rejected": {"files": [], "matches": []},
        }
        self.cutoff = kwargs.get("cutoff", 70)
        self.info_logger = logging.getLogger("info")

    def get_matches(self, type_):
        return self.types[type_]["matches"]

    def match(self, listed, test):
        ratio = self.get_ratio(listed, test)
        return ratio > self.cutoff

    def log_found(self, decoded):
        self.info_logger.info("[FOUND] %s", decoded)
        self.types["unowned"]["matches"].append(decoded)

    def log_rejected(self, key, decoded, file):
        self.types[key]["matches"].append(file)
        self.types["rejected"]["matches"].append(file)
        self.info_logger.info("[%s] %s", key.upper(), decoded)

    def iterate_owned(self, decoded):
        for key, val in self.types.items():
            for file in val["files"]:
                if self.match(decoded, file):
                    self.log_rejected(key, decoded, file)
                    return
        self.log_found(decoded)

    def display_tally(self):
        print(
            f"found: {len(self.types['unowned']['matches'])}    "
            f"rejected: {len(self.types['rejected']['matches'])}",
            end="\r",
            flush=True,
        )

    def iterate(self, magnets):
        self.info_logger.info("Finding wanted torrents")
        try:
            for magnet in magnets:
                self.iterate_owned(magnet)
                self.display_tally()
        except ValueError:
            print("Search returned no results...")
