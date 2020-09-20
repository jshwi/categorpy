Categorpy
=========

.. image:: https://img.shields.io/badge/python-3.8-blue.svg
    :target: https://www.python.org/downloads/release/python-380
    :alt: python3.8
.. image:: https://travis-ci.com/jshwi/categorpy.svg?branch=master
    :target: https://travis-ci.com/jshwi/categorpy
    :alt: travis-ci.com
.. image:: https://readthedocs.org/projects/categorpy/badge/?version=latest
    :target: https://categorpy.readthedocs.io/en/latest/?badge=latest
    :alt: readthedocs.org
.. image:: https://img.shields.io/badge/License-MIT-blue.svg
    :target: https://lbesson.mit-license.org/
    :alt: mit
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: black

`Github Pages <https://jshwi.github.io/categorpy/index.html>`_

.. code-block:: console

    Turbo charged torrent scraper for ``transmission-daemon``

    Scrape entered url for torrents you don't have and automatically load them into the daemon.

    Blacklist files you are not interested in.

    Scans system for files you already own.

    Acknowledges files which are already downloading.
..

.. code-block:: console

    usage: categorpy [-h] [-n] [-u HISTORY] [-p INT or START-END]

    Run with no arguments to scrape the last entered url and begin seeding with `transmission-daemon'.
    Tweak the page number of the url history with the `page' argument - enter either a single page
    number or a range. If no url has been supplied prior, however, the program
    will not be able to run without the `url' argument followed by the url you wish to scrape.

    optional arguments:
      -h, --help                                    show this help message and exit
      -n, --dry                                     only information will be displayed and a download
                                                    will not begin
      -u HISTORY, --url HISTORY                     scrape new url or the last url entered
      -p INT or START-END, --page INT or START-END  scrape a single digit page number or a range e.g. 1-5
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
