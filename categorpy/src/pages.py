"""
pages
=====

Parse the page numbers of selected URL
"""


class Pages:
    """Parse the torrent page-numbers from their URLs

    :param url: The URL the page numbers belong to
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

    def intervals(self):
        """ "Split numbers for a range (if a range is given) otherwise
        nothing happens here and the single digit remains the same
        unpack tuple of low and high numbers
        multiple runs for a start and stop, otherwise this will run only
        once for two values of `0`
        """
        numbers = self.pageno.split("-")
        stopint = 1 if len(numbers) > 1 else 0
        self.start, self.stop = int(numbers[0]), int(numbers[stopint]) + 1
