"""
scrape
======

Scrape the web and parse it's torrents
"""
import re
import sys
from http import client
from urllib import request, parse, error

import bs4

from . import textio


class ScrapeWeb:
    """this contains a method to scrape the web and a method to populate
    an object consisting of a named magnet key and raw magnet data value
    """

    def __init__(self):
        self.soup = bs4.BeautifulSoup
        self.names = []
        self.magnets = []
        self.obj = {}

    def process_request(self, search):
        """Begin the webscraping here

        :param search: Search the web
        """
        header = {"User-Agent": "Mozilla/5.0"}
        try:
            html = request.Request(search, headers=header)
            webpage = request.urlopen(html).read()
            self.soup = bs4.BeautifulSoup(webpage, "html.parser")
        except (client.IncompleteRead, error.URLError) as err:
            _err = str(err).split("] ")
            print(_err[1].replace(">", ""))
            sys.exit(1)

    @staticmethod
    def _cache_results(path, results):
        cacheio = textio.TextIO(
            path, method="replace", args=("_", " "), sort=False
        )
        cacheio.write_list(results)

    def scrape_magnets(self, magnetdata):
        """Extract the usable data from the magnetdata

        :param magnetdata: What has been scraped
        """
        self.magnets = []  # reset
        for result in self.soup("a"):
            href = result.get("href")
            if href and (href.startswith("magnet")):
                self.magnets.append(href)
        self._cache_results(magnetdata, self.magnets)

    def parse_magnets(self, magnetdata):
        """Make sense of the scraped content

        :param magnetdata: Scraped content
        """
        self.obj = {}  # no persistent data when run
        self.scrape_magnets(magnetdata)
        for magnet in self.magnets:
            eq_delim = "".join(magnet.split("=")[2:])
            last_delim = "".join(eq_delim.split("&tr")[:1])
            parsed = parse.unquote(last_delim)
            removelist = "()"
            reparse = re.sub(
                " +", "_", re.sub(r"[^\w" + removelist + "]", " ", parsed)
            )
            self.obj.update({reparse.strip("_"): magnet})
        self.names = self.obj.keys()
