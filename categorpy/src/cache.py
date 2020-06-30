import json
import logging
import os
import re
from fnmatch import fnmatch
from typing import Dict, List

# noinspection PyPackageRequirements
import bencodepy

from . import base


class Cacher:

    template = {"file": [], "link": []}  # type: Dict[str, List[str]]

    def __init__(self, path, paths, parent):
        self.path = path
        self.paths = paths
        self.parent = parent
        self.session = self.cache_index(paths)
        self.index = os.path.join(base.CACHEDIR, parent)

    @staticmethod
    def cache_index(paths):
        obj = dict(Cacher.template)
        for file in paths:
            type_ = "link" if os.path.islink(file) else "file"
            obj[type_].append(file)
        return obj

    def read_cache(self):
        if os.path.isfile(self.index):
            with open(self.index) as json_file:
                cache = json.load(json_file)
            return cache
        return dict(Cacher.template)

    def compare_cache(self, saved):
        return [s for s in saved["file"] if s not in self.session["file"]]

    @staticmethod
    def assume_blacklisted(deleted):
        with open(base.BLACKLIST, "a") as blacklisted:
            for file in deleted:
                blacklisted.write(f"{os.path.basename(file)}\n")

    def _compare_entries(self):
        cache = self.read_cache()
        deleted = self.compare_cache(cache)
        self.assume_blacklisted(deleted)

    def write_cache(self):
        with open(self.index, "w") as json_file:
            json_file.write(json.dumps(self.session, indent=4))

    def cacher(self):
        if os.path.isdir(base.CACHEDIR):
            self._compare_entries()
        else:
            os.mkdir(base.CACHEDIR)
        self.write_cache()


class JSONParse:
    def __init__(self, uncategorized, obj, deadlink):
        self.uncategorized = uncategorized
        self.obj = obj
        self.deadlinks = deadlink

    def remove_ignore_entries(self):
        if os.path.isfile(base.IGNORE):
            ignore = base.parse_file(base.IGNORE)
            self.uncategorized = base.filter_list(self.uncategorized, ignore)

    def parse(self, parent):
        self.remove_ignore_entries()
        deadfiles = {
            "Uncategorized": self.uncategorized,
            "Dead-Link": self.deadlinks,
        }
        for key, value in deadfiles.items():
            if value:
                self.obj[parent][key] = value
        return json.dumps(self.obj, indent=4, sort_keys=True)


class ParseDataFile:
    def __init__(self, file, dirdata):
        self.file = file
        self.dirdata = dirdata
        self.dataobj = {}
        self.parse_blacklist()

    def parse_blacklisted(self, black_list):
        for file in black_list:
            result = file.split("#")
            try:
                self.dataobj.update({result[0].strip(): result[1].strip()})
            except IndexError:
                self.dataobj.update({file: None})

    def append_globs(self):
        for file, comment in list(self.dataobj.items()):
            for focus_file in self.dirdata:
                try:
                    if fnmatch(focus_file.casefold(), file.casefold()):
                        self.dataobj.update({focus_file: comment})
                except re.error as err:
                    log = os.path.join(
                        base.LOGDIR, f"{base.DATE}.{base.TIME}.log"
                    )
                    message = f"[re.error] - {err}\n{file}\n"
                    logging.basicConfig(
                        filename=log,
                        filemode="w",
                        format="%(name)s - %(levelname)s - %(message)s",
                    )
                    logging.warning(message)
                    break

    def parse_blacklist(self):
        if os.path.isfile(self.file):
            filecontent = base.parse_file(self.file)
            self.parse_blacklisted(filecontent)
            self.append_globs()


def parse_torrents(path):
    torrents = []
    for item in os.listdir(path):
        fullpath = os.path.join(path, item)
        with open(fullpath, "rb") as file:
            bencode_file = file.read()
        obj = bencodepy.decode(bencode_file)
        # noinspection PyTypeChecker
        result = obj[b"magnet-info"][b"display-name"]
        decoded = result.decode("utf-8").replace("+", " ")
        torrents.append(decoded)
    return torrents
