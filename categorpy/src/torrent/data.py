import fnmatch
import os
import re

from categorpy.src import base
from categorpy.src.torrent.parse import parse_file


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
                    file = file.replace(" ", "_")
                    if fnmatch.fnmatch(focus_file.casefold(), file.casefold()):
                        self.dataobj.update({focus_file: comment})
                except re.error as err:
                    message = f"re.error - {err}\n{file}\n"
                    base.logger(message, loglevel="warning")
                    break

    def parse_blacklist(self):
        if os.path.isfile(self.file):
            filecontent = parse_file(self.file)
            self.parse_blacklisted(filecontent)
            self.append_globs()
