from urllib import request

import bs4

from categorpy.src import base


class ScrapeWeb:

    header = {"User-Agent": "Mozilla/5.0"}

    def __init__(self, search):
        self.soup = self.process_request(search)
        self.names = []
        self.magnets = []

    @classmethod
    def process_request(cls, search):
        html = request.Request(search, headers=cls.header)
        webpage = request.urlopen(html).read()
        return bs4.BeautifulSoup(webpage, "html.parser")

    @staticmethod
    def _cache_results(path, results):
        text_io = base.TextIO(
            path, method="replace", args=("_", " "), sort=False
        )
        text_io.write(results)

    def scrape_names(self, htmldata):
        for result in self.soup.find_all("a", "detLink"):
            tag = result.get("href")
            result = tag.split("/")[-1]
            self.names.append(result)
        self._cache_results(htmldata, self.names)

    def scrape_magnets(self, magnetdata):
        log = ""
        for result in self.soup("a"):
            href = result.get("href")
            if href and (href.startswith("magnet")):
                self.magnets.append(href)
                log += f"{href}\n"
        base.logger(log)
        self._cache_results(magnetdata, self.magnets)
