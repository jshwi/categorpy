"""
.. code-block:: console

    Turbo charged torrent scraper for ``transmission-daemon``

    Scrape entered url for torrents you don't have and automatically
    load them into the daemon.

    Blacklist files you are not interested in.

    Scans system for files you already own.

    Acknowledges files which are already downloading.
..

.. code-block:: console

    usage: categorpy [-h] [-u HISTORY] [-c 70] [-p INT or START-END]

    Run with no arguments to scrape the last entered url and begin
    seeding with `transmission-daemon'. Tweak the page number of the url
    history with the `page' argument - enter either a single page number
    or a range. If no url has been supplied prior, however, the program
    will not be able to run without the `url' argument followed by the
    url you wish to scrape. Increase or decrease the default cutoff used
    for checking similarity between already owned and blacklisted files.

    optional arguments:
      -h, --help                                    show this help
                                                    message and exit
      -u HISTORY, --url HISTORY                     scrape new url or
                                                    the last url entered
      -c 70, --cutoff 70                            cutoff percentage
                                                    when excluding
                                                    torrents by word
                                                    similarity
      -p INT or START-END, --page INT or START-END  scrape a single
                                                    digit page number or
                                                    a range e.g. 1-5
..

Quick start

.. code-block:: console

    $ # download torrents from one page
    $ categorpy --url "https://www.exampleurl/s/page/1"

    $ # download torrents from alternative page with saved history
    $ categorpy --pages 4  # url now equals \
    $ "https://www.exampleurl/s/page/4"

    $ # download torrents from a range of of pages with cached history
    $ categorpy torrent --pages 1-10
..
"""
