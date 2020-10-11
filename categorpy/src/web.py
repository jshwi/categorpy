"""
categorpy.src.web
=================

https requests, webscraping, downloading - all things web.
"""
import urllib.error
import urllib.request

import bs4

from . import normalize


class Scraper:
    """this contains a method to scrape the web and a method to populate
    an object consisting of a named magnet key and raw magnet data
    value.

    :param header: Header object for requests.
    """

    def __init__(self, header):
        self.names = []
        self.object = {}
        self._header = header
        self._soup = bs4.BeautifulSoup

    def _get_webpage(self, search):
        html = urllib.request.Request(search, headers=self._header)
        webio = urllib.request.urlopen(html)
        return webio.read()

    def process_request(self, search):
        """Begin the webscraping here.

        :param search: Search the web.
        """
        webpage = self._get_webpage(search)
        self._soup = bs4.BeautifulSoup(webpage, "html.parser")

    def _scrape_magnets(self):
        """Extract the usable data from the magnet data."""
        magnets = []
        for result in self._soup("a"):
            href = result.get("href")
            if href and href.startswith("magnet"):
                magnets.append(href)
        return magnets

    def scrape(self):
        """Make sense of the scraped content."""
        self.object.clear()
        magnets = self._scrape_magnets()
        for magnet in magnets:
            name = normalize.Magnet(magnet)
            name.normalize()
            self.names.append(name.magnet)
            self.object.update({name.magnet: magnet})


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
