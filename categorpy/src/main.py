"""
categorpy.src.main
==================
"""

from . import client, exception, find, log, parser


def main():
    """Instantiate ``AppDirs`` and ``AppFiles`` objects for env
    variables

    Instantiate ``textio.TextIO`` object for url search history and pass
    it to ``initialize.Parser`` to handle url args or url history

    Get the ``info`` or ``debug`` loglevel ``logger``, depending on the
    commandline arguments passed

    Handle ``KeyboardInterrupt`` and ``EOFError`` for ``proc`` cleanly
    which is  basically the ``main`` function for this module

    Allow for ``KeyboardInterrupt`` and ``EOFError`` stack-trace to be
    logged of running with ``argparser.args.debug is True``

    This will basically be active as the ``main`` function for this
    module with the actual ``main`` function only defining same
    preliminary variables for the process and catching the verbose
    stack-trace for ``KeyboardInterrupt`` and ``EOFError``

    Record history for the process's url search

    Get the ``transmission-daemon`` ``settings.json`` file as a python
    dictionary object

    Get the instantiated ``find.Find`` object containing the parsed
    blacklist and paths files as well as the indexed paths

    Run the ``transmission`` process

    """
    argparser = parser.Parser()

    log.initialize_loggers(debug=argparser.args.debug)

    args = parser.get_namespace(argparser)

    try:
        findobj = find.analyze_files()
        log.log_time(
            "Finding torrents", client.transmission, args=(args, findobj)
        )
    except (KeyboardInterrupt, EOFError):
        exception.terminate_proc()
