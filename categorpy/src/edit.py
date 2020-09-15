"""
files
=====
"""
import argparse
import os
import subprocess

import object_colors

from . import base

COLOR = object_colors.Color()
COLOR.populate_colors()


# noinspection PyTypeChecker
def argument_parser(*_):
    """Parse the selection of add, view or edit to call the appropriate
    function

    Run action with it's particular process

    The syntax follows the following logic

    .. code-block:: console

        # add entry to FILE=ENTRY
        $ ctgpy files add blacklist="file_not_to_download"

        # view entries in FILE (does not need a value pair)
        $ ctgpy files view blacklist

        # edit the file with a text editor using FILE=EDITOR
        ctgpy files edit blacklist=vim
    ..
    """
    module = COLOR.cyan.get("ctgpy edit")
    parser = argparse.ArgumentParser(
        prog=module,
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog, max_help_position=42
        ),
    )
    add, view, open_ = COLOR.cyan.get("add", "view", "open")
    parser.add_argument(
        "action",
        choices=["add", "view", "open"],
        nargs="+",
        help=(
            f"choices: {add} a quick entry [PATH] [FILE=ENTRY] "
            f"{view} entries [PATH] [FILE] "
            f"{open_} file in selected editor [PATH] [FILE=EDITOR]"
        ),
        default=[],
    )
    parser.add_argument(
        "file",
        metavar="FILE or FILE=STRING",
        nargs="+",
        help="file choices: blacklist, ignore, pack",
    )
    return parser


class ParseKeyword:
    """Parse the keyword argument for argparse into a dictionary object
    from a string

    :param items: The string argument to parse
    """

    def __init__(self, items):
        self.items = items
        self.obj = {}
        self.parse_obj()

    @staticmethod
    def parsekw(keyword):
        """Parse a key, value pair, separated by '='

        :param keyword: Argument entered in the commandline as string
                        that needs to be formatted into a dictionary
        """
        value = None
        keyval = keyword.split("=")
        key = keyval[0].strip()
        if len(keyval) > 1:
            value = "=".join(keyval[1:])
        return {key: value}

    def parse_obj(self):
        """parse a series of key-value pairs and return a dictionary"""
        if self.items:
            for item in self.items:
                self.obj.update(self.parsekw(item))


def add_entry(obj):
    """Add an entry to one of the data files

    :param obj: Dictionary consisting of {"file": "entry"}
    """
    for key, val in obj.items():
        file_path = os.path.join(base.DATADIR, key)
        textio = base.TextIO(file_path)
        textio.append(val)
        COLOR.green.print(f"entry successfully added to {key}")


def view_entries(obj):
    """View the entries entered prior into a data file

    :param obj: Dictionary consisting of {"file": None}
    """
    for key in obj:
        file_path = os.path.join(base.DATADIR, key)
        textio = base.TextIO(file_path)
        textio.read()
        print(textio.output)


def edit_file(obj):
    """Edit a data file with a text editor

    :param obj: Dictionary consisting of {"file": "editor"}
    """
    for key, val in obj.items():
        file_path = os.path.join(base.DATADIR, key)
        subprocess.call(f'{val} "{file_path}"', shell=True)


def valid_file_arg(obj, options):
    """Determine that the argument provided is in line with the
    functions available

    :param obj:     The parse keyword argument
    :param options: The options that are valid
    :return:        True or False for the validity of the argument
    """
    return bool([k for k in obj if k in options])


def main(*argv):
    """Run a selected function if valid argument otherwise notify user

    :param argv:    Function to execute and keyword argument (or just
                    key for view
    """
    parser = argument_parser(*argv)
    args = parser.parse_args()
    action = args.action[0]
    file = args.file
    parsed_object = ParseKeyword(file)
    obj = parsed_object.obj
    options = ("blacklist", "ignore", "pack")
    if valid_file_arg(obj, options):
        if action == "add":
            add_entry(obj)
        elif action == "view":
            view_entries(obj)
        elif action == "open":
            edit_file(obj)
    else:
        COLOR.red.print("file argument must include one of the following:")
        COLOR.cyan.print("- " + "\n- ".join(options))
        parser.print_help()
