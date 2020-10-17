"""
categorpy.__init__
==================

Contains package metadata and exports categorpy.src.main.
"""
try:
    from .src import main
except ModuleNotFoundError:
    pass

__author__ = "Stephen Whitlock"
__maintainer__ = "Stephen Whitlock"
__email__ = "stephen@jshwisolutions.com"
__version__ = "1.0.0"
__copyright__ = "2020, Stephen Whitlock"
__license__ = "MIT"

__all__ = ["main"]
