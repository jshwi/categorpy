import argparse
import os
import subprocess
import sys
from fnmatch import fnmatch

from fuzzywuzzy import fuzz

from . import base


def argument_parser(*_):
    module = base.Print.get_color("categorpy[match]", color=6)
    parser = argparse.ArgumentParser(prog=module)
    parser.add_argument(
        "path",
        action="store",
        help="fullpath to directory you wish to analyze",
    )
    parser.add_argument(
        "-l", "--list", action="store", help="write entry to list arg=editor"
    )
    parser.add_argument(
        "-d",
        "--downloads",
        action="store",
        help="flag files currently downloading",
    )
    parser.add_argument(
        "-b", "--blacklist", action="store", help="add entry to blacklist"
    )
    parser.add_argument()
    parser.add_argument(
        "-a", "--address", action="store", help="web address to scrape"
    )
    _args = parser.parse_args()
    return _args


class FuzzyFind:
    def __init__(self, args):
        self.matched = 0
        self.unmatched = 0
        self.blacklisted = 0
        self.downloading = 0
        self.blackobj = {}
        self.args = args

    @staticmethod
    def match_up(listed, owned):
        test1 = listed == owned
        token = fuzz.token_set_ratio(listed, owned)
        test2 = token > 95
        return test1 or test2

    def parse_blacklisted(self, black_list):
        for file in black_list:
            result = file.split("#")
            try:
                self.blackobj.update({result[0].strip(): result[1].strip()})
            except IndexError:
                self.blackobj.update({file: None})
        return None

    def iterate_owned(self, listed, files, downloads):
        downloading = [d for d in os.listdir(downloads)]
        if listed in self.blackobj:
            self.blacklisted += 1
            blacklisted = base.Print.get_color(
                "[BLACKLISTED]: " + listed, color=1
            )
            if self.blackobj[listed]:
                blacklisted += f"  # {self.blackobj[listed]}"
            del self.blackobj[listed]
            return blacklisted
        if listed in downloading:
            self.downloading += 1
            return base.Print.get_color(listed)
        for file in files:
            if self.match_up(listed, file):
                self.matched += 1
                return base.Print.get_color(listed, color=5)
        self.unmatched += 1
        return base.Print.get_color(listed, color=6)

    def _print_header(self, list_):
        width = len(max(list_, key=len))
        base.Print.color(width * "=", color=2, bold=True)
        print(
            f"{base.Print.get_color(f'UNMATCHED', color=6, bold=True)}: "
            f"{self.unmatched}    "
            f"{base.Print.get_color(f'OWNED', color=5, bold=True)}: "
            f"{self.matched}    "
            f"{base.Print.get_color(f'DOWNLOADING', bold=True)}: "
            f"{self.downloading}    "
            f"{base.Print.get_color(f'BLACKLISTED', color=1, bold=True)}: "
            f"{self.blacklisted}"
        )
        base.Print.color(width * "=", color=2, bold=True)

    def append_globs(self, focus):
        for file, comment in list(self.blackobj.items()):
            for focus_file in focus:
                if fnmatch(focus_file.casefold(), file.casefold()):
                    self.blackobj.update({focus_file: comment})

    @staticmethod
    def write_to_blacklist(write_blacklist, blacklist):
        with open(blacklist, "a") as file:
            file.write(write_blacklist + "\n")

    def main(self):
        match = []
        basenames = []
        path = self.args.path
        blacklist = os.path.join(path, ".blacklist")
        write_blacklist = self.args.blacklist
        if write_blacklist:
            self.write_to_blacklist(write_blacklist, blacklist)
            sys.exit(0)
        cachedir = os.path.join(path, ".cache")
        if not os.path.isdir(cachedir):
            os.mkdir(cachedir)
        file = os.path.join(cachedir, "list")
        downloads = self.args.downloads
        if self.args.list:
            subprocess.call(f'{self.args.list} "{file}"', shell=True)
        if self.args.address:
            base.scraper(self.args.address, file)
        list_ = base.parse_file(file)
        if os.path.isfile(blacklist):
            black_list = base.parse_file(blacklist)
            self.parse_blacklisted(black_list)
            self.append_globs(list_)
        files = base.get_index(path)
        for file in files:
            basenames.append(os.path.basename(file.strip()))
        basenames = [
            f
            for f in basenames
            if f not in (".ignore", ".blacklist", os.path.basename(path))
        ]
        for test_file in list_:
            match.append(self.iterate_owned(test_file, basenames, downloads))
        self._print_header(list_)
        for result in match:
            print(result)


def main(*argv):
    args = argument_parser(*argv)
    fuzzy_find = FuzzyFind(args)
    fuzzy_find.main()
