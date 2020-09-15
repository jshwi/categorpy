Categorpy
=========

.. image:: https://img.shields.io/badge/python-3.8-blue.svg
    :target: https://www.python.org/downloads/release/python-380
    :alt: python3.8
.. image:: https://travis-ci.com/jshwi/categorpy.svg?branch=master
    :target: https://travis-ci.com/jshwi/categorpy
    :alt: travis-ci.com
.. image:: https://img.shields.io/badge/License-MIT-blue.svg
    :target: https://lbesson.mit-license.org/
    :alt: mit
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: black

.. code-block:: console

    usage: ctgpy [-h] {torrent,edit,report,clear} [{torrent,edit,report,clear} ...]

    enter -h all/--help all to see help for all modules

    positional arguments:
      {torrent,edit,report,clear}
                            select module

    optional arguments:
      -h, --help            show this help message and exit
    usage: ctgpy torrent [-h] [-p PATH] [-t TORRENT_DIR] [-u URL] [-n NUMBER or LOW-HIGH] [-i]

    optional arguments:
      -h, --help                                          show this help message and exit
      -p PATH, --path PATH                                fullpath to directory where conflict files may
                                                          belong - if a path is not entered the last
                                                          path given will be used
      -t TORRENT_DIR, --torrent-dir TORRENT_DIR           flag files currently downloading
      -u URL, --url URL                                   web address to scrape (needs to be run at
                                                          least once to generate a cache)
      -n NUMBER or LOW-HIGH, --number NUMBER or LOW-HIGH  search an alternative page number to the
                                                          current selection or loop through a range of
                                                          page numbers e.g. 1-4
      -i, --inspect                                       only information will be displayed and a
                                                          download will not begin
    usage: ctgpy edit [-h] {add,view,open} [{add,view,open} ...] FILE or FILE=STRING
                      [FILE or FILE=STRING ...]

    positional arguments:
      {add,view,open}      choices: add a quick entry [PATH] [FILE=ENTRY] view entries [PATH] [FILE]
                           open file in selected editor [PATH] [FILE=EDITOR]
      FILE or FILE=STRING  file choices: blacklist, ignore, pack

    optional arguments:
      -h, --help           show this help message and exit
    usage: ctgpy report [-h] [-r REVISION]

    optional arguments:
      -h, --help                        show this help message and exit
      -r REVISION, --revision REVISION  number of reports you would like to view (going backwards)
    usage: ctgpy clear [-h] {history} [{history} ...]

    positional arguments:
      {history}   clear contents of data file

    optional arguments:
      -h, --help  show this help message and exit
..
