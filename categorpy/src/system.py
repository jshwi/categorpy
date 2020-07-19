"""
parse
=====

Parse files into human readable data
"""
import os
from pathlib import Path

from . import logger


class Index:
    """Index the files on the user's system and do not stop for
    permission errors

    :param path: The starting path
    """

    def __init__(self, path, logdir):
        self.path = path if path else "/"
        self.root = Path(path)
        self.files = self.iterate()
        self.logger = logger.Logger(logdir, loglevel="debug")

    def exception_handle(self, path):
        """Do not stop scanning the system for the errors below

        :param path: The ``"$PWD"``
        """
        while True:
            try:
                yield next(path)
            except StopIteration:
                self.logger.log(exc_info=True)
                break
            except (FileNotFoundError, OSError, PermissionError):
                self.logger.log(exc_info=True)
                continue

    def iterate(self):
        """get list of system files"""
        return [
            os.path.basename(str(f))
            for f in self.exception_handle(self.root.rglob("*"))
        ]
