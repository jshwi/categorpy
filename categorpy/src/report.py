import argparse
import operator
import os
import subprocess

from categorpy.src import base


def argument_parser(*_):
    module = base.COLOR.cyan.get("ctgpy report")
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(
        prog=module,
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog, max_help_position=55
        ),
    )
    parser.add_argument(
        "-r",
        "--revision",
        action="store",
        default="1",
        help="number of reports you would like to view (going backwards)",
    )
    return parser


def main(*argv):
    files = []
    parser = argument_parser(*argv)
    args = parser.parse_args()
    revision = int(args.revision)
    pathlist = base.get_index(base.DISPLAYDIR)
    try:
        subprocess.call("clear", shell=True)
        fileage = {p: os.path.getctime(p) for p in pathlist}
        for _ in range(0, revision):
            latest = max(fileage.items(), key=operator.itemgetter(1))[0]
            del fileage[latest]
            files.append(latest)
        for latest in files:
            with open(latest) as file:
                header = os.path.basename(latest).replace("display-", "")
                base.COLOR.yellow.print(header)
                print(file.read())
    except ValueError:
        print("There are no reports to view")
