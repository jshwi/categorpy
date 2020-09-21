"""
parse
=====

Parse data files and magnet-links
"""
import logging
import os
import pathlib

# noinspection PyPackageRequirements
import bencodepy

LOGGER = logging.getLogger("categorpy")


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
        textio = TextIO(fullpath)
        textio.read_bytes()
        return textio.output

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
                return None
        except bencodepy.exceptions.BencodeDecodeError:
            return None

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
            if decoded:

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


class Index:
    """Index the files on the user's system and do not stop for
    permission errors
    """

    def __init__(self, paths):
        self.paths = paths
        self.files = []

    def _iterate_each(self, path):
        pathobj = pathlib.Path(path)
        self.files.extend(
            [str(f) for f in pathobj.rglob("*") if os.path.isfile(str(f))]
        )

    def iterate(self):
        """get list of system files"""
        for path in self.paths:
            self._iterate_each(path)
