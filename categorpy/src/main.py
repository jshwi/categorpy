import argparse
import os
import sys

import object_colors

from . import torrent, edit, report, clear, base

MODULES = {
    "torrent": torrent.torrent,
    "edit": edit,
    "report": report,
    "clear": clear,
}


class Parser(argparse.ArgumentParser):

    color = object_colors.Color()
    color.populate_colors()
    prog = color.cyan.get("ctgpy")
    helparg = color.cyan.get("-h all/--help all")

    def __init__(self, *argv):
        super().__init__(
            prog=Parser.prog,
            description=f"enter {Parser.helparg} to see help for all modules",
        )
        self.add_arguments()
        self.args = self.parse_args(argv)

    def add_arguments(self):
        self.add_argument(
            "run",
            choices=list(MODULES.keys()),
            nargs="+",
            help="select module",
            default=[],
        )


def parse_help(argv):
    if len(argv) > 1:
        arg, parameter = argv[0], argv[1]
        if arg in ("-h", "--help") and parameter == "all":
            try:
                parser = Parser(*argv[:1])
                parser.print_help()
            except SystemExit:
                pass
            for key, module in MODULES.items():
                sys.argv = [key, "--help"]
                try:
                    module.main(sys.argv)
                except SystemExit:
                    continue
            sys.exit(0)


def setup_dirs():
    appdirs = [
        base.CACHEDIR,
        base.DATADIR,
        base.LOGDIR,
        base.REPORTDIR,
        base.DISPLAYDIR,
    ]
    userdirs = {k: os.path.isdir(k) for k in appdirs}
    for key in userdirs:
        if not userdirs[key]:
            os.makedirs(key)


def main():
    sys.argv = sys.argv[1:]
    parse_help(sys.argv)
    parser = Parser(*sys.argv[:1])
    prog = parser.args.run[0]
    setup_dirs()
    try:
        for key, module in MODULES.items():
            if prog == key:
                module.main(sys.argv)
    except (KeyboardInterrupt, EOFError):
        print("\u001b[0;31;40mProcess Terminated\u001b[0;0m")
