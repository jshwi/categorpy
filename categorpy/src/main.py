import argparse
import os
import sys

from . import base, configure, jsonmod, match, report


class Parser(argparse.ArgumentParser):

    prog = base.Print.get_color("categorpy", color=6)

    def __init__(self, *argv):
        super().__init__(prog=Parser.prog)
        self.add_arguments()
        self.args = self.parse_args(argv)

    def add_arguments(self):
        self.add_argument(
            "run",
            choices=["json", "match", "report", "configure"],
            nargs="+",
            help="select module",
            default=[],
        )


def main():
    sys.argv = sys.argv[1:]
    parser = Parser(*sys.argv[:1])
    args = parser.args
    prog = args.run[0]
    appdirs = (base.CACHEDIR, base.DATADIR, base.LOGDIR)
    userdirs = {k: os.path.isdir(k) for k in appdirs}
    try:
        for key in userdirs:
            if not userdirs[key]:
                os.mkdir(key)
        if prog == "json":
            jsonmod.main(*sys.argv)
        elif prog == "match":
            match.main(sys.argv)
        elif prog == "report":
            report.main(sys.argv)
        elif prog == "configure":
            configure.main(sys.argv)
    except (KeyboardInterrupt, EOFError):
        print("\u001b[0;31;40mProcess Terminated\u001b[0;0m")
