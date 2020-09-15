"""
parse
=====

Parse files into human readable data
"""
import os
import re
import urllib.parse as urllib

import appdirs

# noinspection PyPackageRequirements
import bencodepy  # this is imported as `bencode.py'

from categorpy.src import base


class ParseTorrents:
    """"""

    def __init__(self, path=None):
        self.path = path
        self.obj = {}
        self.paths = self._get_paths(path)
        self.parse_torrents()

    @staticmethod
    def _torrent_dirs():
        # dictionaries of probable torrent directories
        userconfig_transmission = appdirs.user_config_dir("transmission")
        userconfig_daemon = appdirs.user_config_dir("transmission-daemon")
        libconfig = os.path.join(
            f"{os.sep}var", "lib", "transmission", ".config"
        )
        libconfig_transmission = os.path.join(libconfig, "transmission")
        libconfig_daemon = os.path.join(libconfig, "transmission-daemon")
        return {
            "user": [userconfig_daemon, userconfig_transmission],
            "system": [libconfig_daemon, libconfig_transmission],
        }

    @staticmethod
    def _read_bencode_file(fullpath):
        # read bytes to buffer from file's full path
        textio = base.TextIO(fullpath)
        textio.read_bytes()
        return textio.output

    @staticmethod
    def _parse_bencode_object(bencode):
        # take bencode content (not path) and convert it to human
        # readable text
        obj = bencodepy.decode(bencode)
        # noinspection PyTypeChecker
        result = obj[b"magnet-info"][b"display-name"]
        return result.decode("utf-8").replace("+", " ")

    def _parse_paths(self, torrents):
        # get dictionary of probably torrent directories
        torrent_dirs = self._torrent_dirs()
        for key, values in torrent_dirs.items():

            # searching for `torrents` directory within probable
            # path i.e. `~/.config/transmission-daemon/torrents`
            for value in values:

                # reassign `self.path` to the torrent dir
                self.path = os.path.join(value, "torrents")
                if os.path.isdir(self.path):
                    paths = os.listdir(self.path)

                    # system is the key for system-wide directories
                    # it is likely the user will not have permission to
                    # this directory
                    if key == "system":
                        try:
                            with open(os.path.join(self.path, paths[0])) as f:
                                _ = f.read()
                            torrents.extend(paths)
                        except (FileNotFoundError, PermissionError):
                            pass
                        break
        return torrents

    def _get_paths(self, path):
        # if the path the user has entered is valid then use that path
        if path:
            return os.listdir(path)

        # otherwise test the probably torrent paths for results
        return self._parse_paths(torrents=[])

    def parse_torrents(self):
        for path in self.paths:
            fullpath = os.path.join(self.path, path)

            # get the bencode bytes from their .torrent file
            bencode = self._read_bencode_file(fullpath)

            # parse these bytes into human readable plaintext
            decoded = self._parse_bencode_object(bencode)

            # update the torrent file object with the torrent file's
            # name as the key and it's path as the value
            self.obj.update({decoded: os.path.basename(path)})


class ParsePageNumber:
    def __init__(self, url):
        self.url = url
        self.ulist = self.url.split("/")
        self.ispage = False
        self.page_index = 0
        self.check_for_pages()

    def check_for_pages(self):
        try:
            self.page_index = self.ulist.index("page") + 1
            self.ispage = True
        except ValueError:
            pass

    def _replace_page(self, page_number):
        self.ulist[self.page_index] = str(page_number)

    def select_page_number(self, page_number):
        self._replace_page(page_number)
        return "/".join(self.ulist)

    def get_page_number(self):
        return self.ulist[self.page_index] if self.ispage else "0"


def parse_file(path):
    """Read a file into this session and attempt to resolve any
    non-critical errors

    If no content can be retrieved return an empty list

    :param path:    the file path to read from
    :return:        A list of the file's content
    """
    textio = base.TextIO(path)
    if os.path.isfile(path):
        return textio.read_to_list()
    parent = os.path.basename(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    textio.touch()
    return []


def parse_magnets(magnets):
    reparsed = []
    for magnet in magnets:
        eq_delim = "".join(magnet.split("=")[2:])
        last_delim = "".join(eq_delim.split("&tr")[:1])
        parsed = urllib.unquote(last_delim)
        removelist = "()"
        reparse = re.sub(
            " +", "_", re.sub(r"[^\w" + removelist + "]", " ", parsed)
        )
        reparsed.append(reparse.strip("_"))
    return reparsed
