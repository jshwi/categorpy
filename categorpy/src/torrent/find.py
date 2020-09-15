"""
find
====

System file matching
"""
import os

import object_colors
import rapidfuzz

from categorpy.src import base


class FuzzyFind:
    """Exclude unwanted files from downloading

    :param files:       System files
    :param downloads:   existing downloads
    :param pack:        Directories which have been downloaded (in the
                        case that it has been broken up into individual
                        files)
    """

    def __init__(self, blacklist, files, downloads, pack):
        self.types = {
            "matched": {
                "count": 0,
                "color": 5,
                "list": files,
                "bullet": "[  MATCHED  ]",
                "head": "OWNED",
            },
            "unmatched": {
                "count": 0,
                "color": 6,
                "list": [],
                "bullet": "[ UNMATCHED ]",
                "head": "UNMATCHED",
            },
            "blacklisted": {
                "count": 0,
                "color": 1,
                "list": blacklist,
                "bullet": "[BLACKLISTED]",
                "head": "BLACKLISTED",
            },
            "downloading": {
                "count": 0,
                "color": 3,
                "list": downloads,
                "bullet": "[DOWNLOADING]",
                "head": "PACKAGE",
            },
            "pack": {
                "count": 0,
                "color": 4,
                "list": pack,
                "bullet": "[PACK]",
                "head": "PACK",
            },
        }

    def _color_str(self, key, val):
        color_code = self.types[key]["color"]
        color = object_colors.Color(text=color_code, effect="bold")
        return color.get(self.types[key][val])

    # noinspection PyArgumentList
    @staticmethod
    def _match_up(listed, owned):
        return listed == owned or bool(
            rapidfuzz.fuzz.token_set_ratio(listed, owned, score_cutoff=95)
        )

    @staticmethod
    def _container(url, string, color):
        sep = 80 * "-"
        sep = base.COLOR.green.get(sep) if color else sep
        address = base.COLOR.blue.get(url) if color else url
        return f"{sep}\n{string}\n{sep}\n{address}\n"

    @staticmethod
    def _write_report(path, name, report):
        fullpath = os.path.join(path, name)
        textio = base.TextIO(fullpath)
        textio.write(report)

    def unmatched(self):
        return self.types["unmatched"]["list"]

    def _increment(self, key):
        self.types[key]["count"] += 1

    def _report_line(self, key, listed):
        bullet = self.types[key]["bullet"]
        colbullet = f"{self._color_str(key, 'bullet')}"
        return f"{bullet} {listed}", f"{colbullet} {listed}"

    def _iterate_owned(self, listed):
        for type_ in self.types:
            if type_ != "unmatched":
                for item in self.types[type_]["list"]:
                    if self._match_up(listed, item):
                        self._increment(type_)
                        return self._report_line(type_, listed)
        self.types["unmatched"]["list"].append(listed)
        self._increment("unmatched")
        return self._report_line("unmatched", listed)

    def _header(self, url):
        header, colheader = "", ""
        for head, obj in self.types.items():
            header += f"{obj['head']}: {obj['count']}    "
            colheader += f"{self._color_str(head, 'head')}: {obj['count']}    "
        header_str = self._container(url, f"{header}", color=False)
        colheader_str = self._container(url, f"{colheader}", color=True)
        return header_str, colheader_str

    def report(self, url, names):
        match, colmatch = zip(*[self._iterate_owned(f) for f in names])
        report, colreport = self._header(url)
        for (result, colresult) in zip(match, colmatch):
            report += f"{result}\n"
            colreport += f"{colresult}\n"
        self._write_report(base.REPORTDIR, f"report-{base.SUFFIX}", report)
        self._write_report(
            base.DISPLAYDIR, f"display-{base.SUFFIX}", colreport
        )
        return report, colreport
