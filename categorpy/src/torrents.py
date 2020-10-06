"""
parse
=====

Parse data files and magnet-links.
"""
import http.client
import os
import urllib.error
import urllib.request

# noinspection PyPackageRequirements
import bencodepy
import bs4

from . import locate, log, normalize, textio


class Scrape:
    """this contains a method to scrape the web and a method to populate
    an object consisting of a named magnet key and raw magnet data
    value.
    """

    def __init__(self):
        self.header = {"User-Agent": "Mozilla/5.0"}
        self.soup = bs4.BeautifulSoup
        self.magnets = []
        self.object = {}

    def _get_webpage(self, search):
        html = urllib.request.Request(search, headers=self.header)
        webio = urllib.request.urlopen(html)
        return webio.read()

    def process_request(self, search):
        """Begin the webscraping here.

        :param search: Search the web.
        """
        try:
            webpage = self._get_webpage(search)
            self.soup = bs4.BeautifulSoup(
                markup=webpage, features="html.parser"
            )
        except (
            http.client.IncompleteRead,
            urllib.error.URLError,
            http.client.RemoteDisconnected,
        ) as err:
            errlogger = log.get_logger("error")
            print(f"\u001b[0;31;40m{err}\u001b[0;0m")
            errlogger.exception(str(err))

    def scrape_magnets(self):
        """Extract the usable data from the magnet data."""
        self.magnets.clear()
        for result in self.soup(markup="a", features="html.parser"):
            href = result.get("href")
            if href and href.startswith("magnet"):
                self.magnets.append(href)

    def parse_magnets(self):
        """Make sense of the scraped content."""
        self.object.clear()
        for magnet in self.magnets:
            name = normalize.Magnet(magnet)
            name.normalize()
            self.object.update({name.magnet: magnet})

    def get_names(self):
        """Return a list of scraped names.

        :return: List of magnet names.
        """
        return list(self.object.keys())


class Read:
    """Parse downloaded data for human readable categorisation."""

    errlogger = log.get_logger("error")

    def __init__(self):
        self.client_dir = locate.APP.client_dir
        self.path = os.path.join(self.client_dir, "torrents")
        self.paths = []
        self.object = {}
        self._get_torrent_paths()

    def _get_torrent_paths(self):
        """Get the torrent magnet-link files.

        :return: List of torrent magnet-links.
        """
        if os.path.isdir(self.path):
            self.paths.extend(
                [os.path.join(self.path, t) for t in os.listdir(self.path)]
            )

    @staticmethod
    def _read_bencode_file(fullpath):
        # read bytes to buffer from file's full path
        fullpathio = textio.TextIO(fullpath)
        fullpathio.read_bytes()
        return fullpathio.output

    @classmethod
    def parse_bencode_object(cls, bencode):
        """take bencode content (not path) and convert it to human
        readable text.

        :param bencode: Bytes read from torrent file.
        """
        try:
            obj = bencodepy.decode(bencode)
            try:
                # noinspection PyTypeChecker
                result = obj[b"magnet-info"][b"display-name"]
                return result.decode("utf-8").replace("+", " ")
            except KeyError as err:
                cls.errlogger.exception(str(err))
                return None
        except bencodepy.exceptions.BencodeDecodeError as err:
            cls.errlogger.exception(str(err))
            return None

    def parse_torrents(self):
        """Call to get the readable content from the bencode and create
        a dictionary object of names and their corresponding magnets.
        """
        for path in self.paths:
            try:
                # get the bencode bytes from their .torrent file
                bencode = self._read_bencode_file(path)
            except IsADirectoryError as err:
                self.errlogger.exception(str(err))
                continue

            # parse these bytes into human readable plaintext
            decoded = self.parse_bencode_object(bencode)
            if decoded:

                # update the torrent file object with the torrent file's
                # name as the key and it's path as the value
                self.object.update({decoded: os.path.basename(path)})

    def get_decoded_names(self):
        """Return a list of decoded names.

        :return: List of decoded magnet names.
        """
        return list(self.object.keys())


class Pages:
    """Parse the torrent page-numbers from their URLs.

    :param url:     The URL the page numbers belong to.
    :param pageno:  A value if passed via the commandline otherwise it
                    will be assigned later with
                    ``self.get_page_number``.
    """

    def __init__(self, url, pageno):
        self.url = url
        self.pageno = pageno
        self.ulist = self.url.split("/")
        self.ispage = False
        self.page_index = 0
        self.start = 0
        self.stop = 0
        self._set()

    def _set(self):
        self.check_for_pages()
        self.pageno = self.pageno if self.pageno else self.get_page_number()
        self.intervals()

    def check_for_pages(self):
        """Check for the page schema of the URL."""
        try:
            self.page_index = self.ulist.index("page") + 1
            self.ispage = True
        except ValueError:
            pass

    def _replace_page(self, page_number):
        self.ulist[self.page_index] = str(page_number)

    def page_number(self, page_number):
        """Alter the URL to replace the current page number with the
        desired page-number.

        :param page_number: Alternative page number to the current
                            URL's.
        """
        self._replace_page(page_number)
        return "/".join(self.ulist)

    def get_page_number(self):
        """Extract the page-number from the URL.

        :return: Page-number.
        """
        return self.ulist[self.page_index] if self.ispage else "0"

    def intervals(self):
        """ "Split numbers for a range (if a range is given) otherwise
        nothing happens here and the single digit remains the same.
        Unpack tuple of low and high numbers - multiple runs for a start
        and stop, otherwise this will run only once with two instances
        of ``0``.
        """
        numbers = self.pageno.split("-")
        stopint = 1 if len(numbers) > 1 else 0
        self.start, self.stop = int(numbers[0]), int(numbers[stopint]) + 1
