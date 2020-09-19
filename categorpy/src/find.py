"""
find
====

System file matching
"""
import logging
import os
import re
from collections import OrderedDict

from . import textio


class Find:
    """Exclude unwanted files from downloading

    :key owned:       System files
    :key downloading: existing downloads
    :key pack:        Directories which have been downloaded (in the
                        case that it has been broken up into individual
                        files)
    """

    def __init__(self, cachedir, **kwargs):
        self.types = OrderedDict(
            [
                (
                    "blacklisted",
                    {
                        "count": 0,
                        "color": 1,
                        "list": kwargs.get("blacklisted", {}),
                        "magnet": [],
                        "bullet": "[BLACKLISTED]",
                        "head": "BLACKLISTED",
                    },
                ),
                (
                    "downloading",
                    {
                        "count": 0,
                        "color": 3,
                        "list": kwargs.get("downloading", []),
                        "magnet": [],
                        "bullet": "[DOWNLOADING]",
                        "head": "DOWNLOADING",
                    },
                ),
                (
                    "pack",
                    {
                        "count": 0,
                        "color": 4,
                        "list": kwargs.get("pack", []),
                        "magnet": [],
                        "bullet": "[   PACK    ]",
                        "head": "PACK",
                    },
                ),
                (
                    "owned",
                    {
                        "count": 0,
                        "color": 5,
                        "list": kwargs.get("owned", []),
                        "magnet": [],
                        "bullet": "[   OWNED   ]",
                        "head": "OWNED",
                    },
                ),
            ]
        )
        self.unmatched = {
            "unmatched": {
                "count": 0,
                "color": 6,
                "list": [],
                "magnet": [],
                "bullet": "[ UNMATCHED ]",
                "head": "UNMATCHED",
            }
        }
        self.cutoff = 70
        self.ratios = {}
        self.logger = logging.getLogger("info")
        self.cachedir = cachedir

    exclude = ["and"]

    def _global_dict(self, key):
        if key == "unmatched":
            return self.unmatched[key]
        return self.types[key]

    def _increment(self, key):
        self._global_dict(key)["count"] += 1

    def _append(self, key, val, item):
        self._global_dict(key)[val].append(item)

    @staticmethod
    def _container(url, string):
        sep = 80 * "-"
        return f"{sep}\n{string}\n{sep}\n{url}\n"

    def _report_line(self, key, listed):
        if key == "unmatched":
            bullet = self.unmatched[key]["bullet"]
        else:
            bullet = self.types[key]["bullet"]
        return f"{bullet} {listed}"

    @staticmethod
    def _format_blacklisted(type_, files, file, listed):
        if type_ == "blacklisted" and files[file]:
            comment = f"# {files[file]}"
            listed = f"{listed}  {comment}"
        return listed

    def _header(self, url):
        header = ""
        for _, val in self.types.items():
            header += f"{val['head']}: {val['count']}    "
        return self._container(url, f"{header}")

    def _reset_counters(self):
        # Reset the counters that are displayed in the report for the
        # amount of files that have matched from any of the type's lists
        for type_, _ in zip(self.types, self.unmatched):
            self.types[type_]["count"] = 0

    def _iterate_owned(self, listed):
        for type_ in self.types:
            files = self.types[type_]["list"]
            for file in files:
                if self.match(listed, file, type_):
                    self._increment(type_)
                    listed = self._format_blacklisted(
                        type_, files, file, listed
                    )
                    self._append(type_, "magnet", listed)
                    return self._report_line(type_, listed)
        self._append("unmatched", "list", listed)

        self._increment("unmatched")
        return self._report_line("unmatched", listed)

    def _capture(self, listed, ratio, type_):
        if listed in self.ratios and ratio < self.ratios[listed]:
            return
        self.ratios.update({f"{type_}={listed}": ratio})

    def match(self, listed, test, type_):
        """Match the `blacklist`, `downloads`, `matched` and `pack`
        strings against scraped filenames for the web

        The `blacklist` list is manually configured by the user and is
        run first in the ordered dictionary to discard any files the
        user does not want to harvest

        The `downloads` list consists of names belonging to parsed
        torrent files existing on the user's system and requires no
        manual intervention by the user

        The `matched` list consists of the user's files on their system
        and like the `downloads` list requires no manual intervention
        by the user

        The `pack` list consists of (at this point in time) user entered
        directories that have been downloaded buy no longer exist i.e.
        the user emptied the directory and divided the files

        Allow some margin of error to account for slight variances in
        how files are downloaded and saved and displayed online

        :param type_:
        :param listed:  The magnet (name extracted) iterated from a list
                        of files that will potentially be scraped from
                        the web

        :param test:    Any one of the files from the `self.types` list
                        that determine whether a download should not
                        occur

                        All these lists will only be used if a match is
                        found, so while the `matched` list is named so,
                        it is only really a match if the file matched
                        with a scraped file

                        It is worth noting, too, that `blacklisted`,
                        `downloading` and `pack` are also only relevant
                        if there is a match (and while  they too are
                        matches it is not their defining feature)
        :return:        A boolean value for whether the magnet file has
                        satisfied the fuzzy search against a listed item
        """
        write_ratio = os.path.join(self.cachedir, "ratio")
        strings = self._normalize([listed, test])
        ratio = self._word_ratio(*strings, type_)
        ratioio = textio.TextIO(write_ratio)
        ratioio.append(f"{listed}: {ratio}\n")
        self._capture(listed, ratio, type_)
        return ratio > self.cutoff

    @staticmethod
    def _strip(string):
        return re.sub(r"([^\s\w]|_)+", " ", string)

    def _normalize(self, strings):
        for index_, string in enumerate(strings):
            replace = string.casefold().replace("_", " ").replace(".", " ")
            regex = self._strip(replace)
            strings[index_] = " ".join(regex.split())
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

    def _word_ratio(self, string1, string2, _):
        word_count = {
            w: string2.split().count(w)
            for w in string1.split()
            if w not in Find.exclude
        }
        match_len = [len(k * v) for k, v in word_count.items()]
        percent_match = self._work_percentage(string1, match_len)
        return 100 * percent_match

    def filelist(self, key, val):
        """Get a list of paths from any of the existing types in the
        instance dictionary

        Makes these values more easily accessible as the only values
        that may need to be accessed outside the instance

        :key:       blacklisted, downloading, pack, match or unmatched
        :return:    A list belonging to any one of the above keys passed
                    to the method
        """
        return self._global_dict(key)[val]

    def iterate(self, magnet_names, url=None):
        """Iterate through the list of names parsed from a dictionary of
        magnets

        The number's for the reported matched will have been collected
        and so the counter is reset

        :param url:
        :param magnet_names:    Strings of human readable names for the
                                magnets scraped from the web that can
                                matched against real files and user
                                entries
        """
        try:
            header = self._header(url)
            report = "\n".join([self._iterate_owned(f) for f in magnet_names])
            self.logger.info(f"\n{header}\n{report}")
            self._reset_counters()
        except ValueError:
            print("Search returned no results...")
