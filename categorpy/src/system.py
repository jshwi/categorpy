"""
parse
=====

Parse files into human readable data
"""
import logging
import os
from pathlib import Path


class Index:
    """Index the files on the user's system and do not stop for
    permission errors

    :param path: The starting path
    """

    def __init__(self, path):
        self.path = path if path else "/"
        self.root = Path(path)
        self.logger = logging.getLogger("debug")
        self.files = self.iterate()

    def exception_handle(self, path):
        """Do not stop scanning the system for the errors below

        :param path: The ``"$PWD"``
        """
        while True:
            try:
                yield next(path)
            except StopIteration:
                self.logger.debug("", exc_info=True)
                break
            except (FileNotFoundError, OSError, PermissionError):
                self.logger.debug("", exc_info=True)
                continue

    def iterate(self):
        """get list of system files"""
        return [
            os.path.basename(str(f))
            for f in self.exception_handle(self.root.rglob("*"))
        ]
