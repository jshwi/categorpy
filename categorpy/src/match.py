import argparse
import errno
import os
import sys

from appdirs import user_config_dir
from rapidfuzz import fuzz

from . import base, cache


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


class Find:
    def __init__(self, address, files, downloads, pack, blackobj):
        self.address = address
        self.files = files
        self.downloads = downloads
        self.pack = pack
        self.count = {
            "matched": 0,
            "unmatched": 0,
            "blacklisted": 0,
            "downloading": 0,
            "pack": 0,
        }
        self.blackobj = blackobj

    @staticmethod
    def match_up(listed, owned):
        test1 = listed == owned
        token = fuzz.token_set_ratio(listed, owned)
        test2 = token > 95
        return test1 or test2

    def iterate_owned(self, listed):
        if listed in self.blackobj:
            self.count["blacklisted"] += 1
            blacklisted = base.Print.get_color(
                "[BLACKLISTED]: " + listed, color=1
            )
            if self.blackobj[listed]:
                blacklisted += f"  # {self.blackobj[listed]}"
            del self.blackobj[listed]
            return blacklisted
        for file in self.files:
            if self.match_up(listed, file):
                self.count["matched"] += 1
                return base.Print.get_color(listed, color=5)
        for download in self.downloads:
            if self.match_up(listed, download):
                self.count["downloading"] += 1
                return base.Print.get_color(listed)
        for pack in self.pack:
            if self.match_up(listed, pack):
                self.count["pack"] += 1
                return base.Print.get_color(listed, color=4)
        self.count["unmatched"] += 1
        return base.Print.get_color(listed, color=6)

    @staticmethod
    def _container(string):
        sep = base.Print.get_color(75 * "=", color=2, bold=True)
        return f"{sep}\n{string}\n{sep}"

    def _format_header(self):
        header = ""
        types = {
            "UNMATCHED": {"color": 6, "count": self.count["unmatched"]},
            "OWNED": {"color": 5, "count": self.count["matched"]},
            "DOWNLOADING": {"color": 3, "count": self.count["downloading"]},
            "BLACKLISTED": {"color": 1, "count": self.count["blacklisted"]},
            "PACKAGE": {"color": 4, "count": self.count["pack"]},
        }
        for head, obj in types.items():
            header += base.Print.get_color(head, color=obj["color"], bold=True)
            header += f": {obj['count']}    "
        return header

    def print_header(self):
        header = self._format_header()
        formatted = self._container(header)
        print(formatted)

    @staticmethod
    def write_to_blacklist(write_blacklist, blacklist):
        with open(blacklist, "a") as file:
            file.write(write_blacklist + "\n")


def parse_torrent_path(downloads_path):
    if not os.path.isdir(downloads_path):
        guess_dir = os.path.join(user_config_dir(downloads_path), "torrent")
        if not os.path.isdir(guess_dir):
            err = FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), downloads_path
            )
            base.Print.color(err, color=1)
            print("cannot find selected torrent directory")
            sys.exit(1)
    return downloads_path


def main(*argv):
    parser = argument_parser(*argv)
    args = parser.parse_args()
    path = args.path
    downloads_path = parse_torrent_path(args.downloads)
    downloads = cache.parse_torrents(downloads_path)
    address = args.address
    pack = base.parse_file(base.PACK)
    ignore = base.parse_file(base.IGNORE)
    files = base.get_index(path)
    files = [os.path.basename(f) for f in files]
    if address:
        base.scraper(args.address, base.HTTP)
    http = base.parse_file(base.HTTP)
    parse_datafile = cache.ParseDataFile(base.BLACKLIST, http)
    blackobj = parse_datafile.dataobj
    find = Find(address, files, downloads, pack, blackobj)
    if address:
        base.scraper(args.address, base.IGNORE)
    match = [find.iterate_owned(f) for f in ignore]
    find.print_header()
    for result in match:
        print(result)
