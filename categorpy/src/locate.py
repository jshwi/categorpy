"""
categorpy.src.locate
====================

Define environment for navigating system.
"""
import os
import pathlib

import appdirs

APPNAME = "categorpy"


class AppDirs(appdirs.AppDirs):
    """Application directories for package inheriting ``AppDirs`` from
    module ``appdirs``.
    """

    def __init__(self):
        super().__init__(appname=APPNAME)
        self._initialize_appdirs()
        self.user_config_dirname = os.path.dirname(self.user_config_dir)
        self.client_dir = os.path.join(
            self.user_config_dirname, "transmission-daemon"
        )

    def _initialize_appdirs(self):
        # create directories for persistent data storage for app.
        dirs = [self.user_cache_dir, self.user_config_dir, self.user_log_dir]
        for _dir in dirs:
            path = pathlib.Path(_dir)
            path.mkdir(parents=True, exist_ok=True)


class AppFiles(AppDirs):
    """Application file paths inheriting ``AppDirs`` for directory
    paths.
    """

    def __init__(self):
        super().__init__()
        self.histfile = os.path.join(self.user_cache_dir, "history")
        self.blacklist = os.path.join(self.user_config_dir, "blacklist")
        self.paths = os.path.join(self.user_config_dir, "paths")
        self.config = os.path.join(self.user_config_dir, "config.ini")
        self.torrents = os.path.join(self.client_dir, "torrents")
        self.settings = os.path.join(self.client_dir, "settings.json")
        self._initialize_appfiles()

    def _initialize_appfiles(self):
        # create empty files for persistent data storage for app so user
        # knows what files will be recognised by the process
        files = [self.histfile, self.blacklist]
        for file in files:
            path = pathlib.Path(file)
            path.touch()


APP = AppFiles()
