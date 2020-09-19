"""
parse
=====

Parse data files and magnet-links
"""
import fnmatch
import logging
import os
import re

# noinspection PyPackageRequirements
import bencodepy

from . import textio


class Torrents:
    """Parse downloaded data for human readable categorisation

    :param path: Dirs that contain downloaded torrent magnet-links
    """

    def __init__(self, path):
        self.path = path
        self.files = []
        self.obj = {}

    def get_torrents(self):
        """Get the torrent magnet-link files

        :return: List of torrent magnet-links
        """
        if os.path.isdir(self.path):
            self.files.extend(
                [os.path.join(self.path, t) for t in os.listdir(self.path)]
            )
        return self.files

    @staticmethod
    def _read_bencode_file(fullpath):
        # read bytes to buffer from file's full path
        fullpathio = textio.TextIO(fullpath)
        fullpathio.read_bytes()
        return fullpathio.output

    @staticmethod
    def _parse_bencode_object(bencode):
        # take bencode content (not path) and convert it to human
        # readable text
        try:
            obj = bencodepy.decode(bencode)
            try:
                # noinspection PyTypeChecker
                result = obj[b"magnet-info"][b"display-name"]
                return result.decode("utf-8").replace("+", " ")
            except KeyError:
                return ""
        except bencodepy.exceptions.BencodeDecodeError:
            return ""

    def parse_torrents(self):
        """Call to get the readable content from the bencode and create
        a dictionary object of names and their corresponding magnets
        """
        self.get_torrents()
        for path in self.files:
            try:
                # get the bencode bytes from their .torrent file
                bencode = self._read_bencode_file(path)
            except IsADirectoryError:
                continue

            # parse these bytes into human readable plaintext
            decoded = self._parse_bencode_object(bencode)

            # update the torrent file object with the torrent file's
            # name as the key and it's path as the value
            self.obj.update({decoded: os.path.basename(path)})


class PageNumbers:
    """Parse the torrent page-numbers from their URLs

    :param url: The URL the page numbers belong to
    """

    def __init__(self, url):
        self.url = url
        self.ulist = self.url.split("/")
        self.ispage = False
        self.page_index = 0
        self.check_for_pages()

    def check_for_pages(self):
        """Check for the page schema of the URL"""
        try:
            self.page_index = self.ulist.index("page") + 1
            self.ispage = True
        except ValueError:
            pass

    def _replace_page(self, page_number):
        self.ulist[self.page_index] = str(page_number)

    def select_page_number(self, page_number):
        """Alter the URL to replace the current page number with the
        desired page-number
        """
        self._replace_page(page_number)
        return "/".join(self.ulist)

    def get_page_number(self):
        """Extract the page-number from the url

        :return: Page-number
        """
        return self.ulist[self.page_index] if self.ispage else "0"


class Saved:
    """Extract information from the saved data-file to influence present
    downloads
    """

    def __init__(self, filename, datadir):
        self.file = os.path.join(datadir, filename)
        self.files = []
        self.obj = {}
        self.logger = logging.getLogger("warning")
        self.textio = textio.TextIO(self.file)
        self.textio.touch()

    def append_globs(self, magnets):
        """Append files matching globs which are supported in certain
        data-files

        :param magnets: Match the globs against the magnet-files to
                        filter out the unwanted magnets
        """
        for file, comment in list(self.obj.items()):
            for focus_file in magnets:
                try:
                    file = file.replace(" ", "_")
                    if fnmatch.fnmatch(focus_file.casefold(), file.casefold()):
                        self.obj.update({focus_file: comment})
                except re.error as err:
                    self.logger.warning(f"re.error - {err}\n{file}\n")
                    break

    def _blacklisted(self):
        for file in self.files:
            result = file.split("#")
            try:
                self.obj.update({result[0].strip(): result[1].strip()})
            except IndexError:
                self.obj.update({file: None})

    def parse_file(self):
        """Read a file into this session and attempt to resolve any
        non-critical errors

        If no content can be retrieved return an empty list

        :return:        A list of the file's content
        """
        lis = self.textio.read_to_list()
        self.files.extend(lis)

    def parse_blacklist(self, magnets):
        """Parse the blacklist to exclude magnets which have been
        blacklisted

        :param magnets: Magnets that will be loaded to ``transmission``
                        if they have not been blacklisted
        """
        self.parse_file()
        self._blacklisted()
        self.append_globs(magnets)
