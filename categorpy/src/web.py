"""
scrape
======

Scrape the web and parse it's torrents
"""
from http import client
from urllib import request, error

import bs4

from . import exception, normalize


class ScrapeWeb:
    """this contains a method to scrape the web and a method to populate
    an object consisting of a named magnet key and raw magnet data value
    """

    def __init__(self):
        self.soup = bs4.BeautifulSoup
        self.magnets = []
        self.object = {}

    def process_request(self, search):
        """Begin the webscraping here

        :param search: Search the web
        """
        header = {"User-Agent": "Mozilla/5.0"}
        try:
            html = request.Request(search, headers=header)
            webio = request.urlopen(html)
            webpage = webio.read()
            self.soup = bs4.BeautifulSoup(webpage, "html.parser")
        except (
            client.IncompleteRead,
            error.URLError,
            client.RemoteDisconnected,
        ) as err:
            exception.exit_error(err)

    def scrape_magnets(self):
        """Extract the usable data from the magnetdata"""
        self.magnets.clear()
        for result in self.soup("a"):
            href = result.get("href")
            if href and (href.startswith("magnet")):
                self.magnets.append(href)

    def parse_magnets(self):
        """Make sense of the scraped content"""
        self.object.clear()
        for magnet in self.magnets:
            name = normalize.Magnet(magnet)
            name.normalize()
            self.object.update({name.magnet: magnet})

    def get_scraped_keys(self):
        """Return a list of scraped names

        :return: List of magnet names
        """
        return list(self.object.keys())
