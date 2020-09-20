"""
scrape
======

Scrape the web and parse it's torrents
"""
import logging
import sys
from http import client
from urllib import request, error

import bs4

from . import normalize

ERRLOGGER = logging.getLogger("error")


class ScrapeWeb:
    """this contains a method to scrape the web and a method to populate
    an object consisting of a named magnet key and raw magnet data value
    """

    def __init__(self):
        self.soup = bs4.BeautifulSoup
        self.magnets = []
        self.obj = {}

    @staticmethod
    def url_error(err):
        ERRLOGGER.error(msg="", exc_info=True)
        _err = str(err).split("] ")
        print(_err[1].replace(">", ""))
        sys.exit(1)

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
            self.url_error(err)

    def scrape_magnets(self):
        """Extract the usable data from the magnetdata"""
        self.magnets = []  # reset
        for result in self.soup("a"):
            href = result.get("href")
            if href and (href.startswith("magnet")):
                self.magnets.append(href)

    def parse_magnets(self):
        """Make sense of the scraped content"""
        for magnet in self.magnets:
            name = normalize.Magnet(magnet)
            name.normalize()
            self.obj.update({name.magnet: magnet})
