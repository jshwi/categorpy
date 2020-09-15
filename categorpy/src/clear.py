import os

import object_colors

from . import base

COLOR = object_colors.Color()
COLOR.populate_colors()


FILEOBJ = {"history": base.HISTORY}


def argument_parser(*_):
    parser = base.base_parser("clear")
    parser.add_argument(
        "files",
        choices=list(FILEOBJ.keys()),
        nargs="+",
        help="clear contents of data file",
        default=[],
    )
    return parser


def main(*argv):
    parser = argument_parser(*argv)
    args = parser.parse_args()
    for file in args.files:
        os.remove(FILEOBJ[file])
        COLOR.green.print(f"{file} cleared")
