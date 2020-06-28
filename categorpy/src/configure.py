import argparse
import os
import subprocess

from . import base


def argument_parser(*_):
    module = base.Print.get_color("categorpy[configure]", color=6)
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(
        prog=module,
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog, max_help_position=42
        ),
    )
    add = base.Print.get_color("add", color=6)
    view = base.Print.get_color("view", color=6)
    edit = base.Print.get_color("edit", color=6)
    parser.add_argument(
        "action",
        choices=["add", "view", "edit"],
        nargs="+",
        help=(
            f"choices: {add} a quick entry [PATH] [FILE=ENTRY] "
            f"{view} entries [PATH] [FILE] "
            f"{edit} file in selected editor [PATH] [FILE=EDITOR]"
        ),
        default=[],
    )
    parser.add_argument("path", action="store", help="fullpath to directory")
    parser.add_argument(
        "file",
        metavar="FILE or FILE=STRING",
        nargs="+",
        help="file choices: blacklist, ignore, pack",
    )
    return parser


def write_to_blacklist(write_blacklist, blacklist):
    with open(blacklist, "a") as file:
        file.write(write_blacklist + "\n")


def add_entry(cachedir, obj):
    for key, val in obj.items():
        file_path = os.path.join(cachedir, key)
        write_to_blacklist(val, file_path)
        base.Print.color(f"entry successfully added to {key}", color=2)


def view_entries(cachedir, obj):
    for key in obj:
        file_path = os.path.join(cachedir, key)
        with open(file_path) as file:
            file = file.read().splitlines()
            for line in file:
                print(line)


def edit_file(cachedir, obj):
    for key, val in obj.items():
        file_path = os.path.join(cachedir, key)
        subprocess.call(f'{val} "{file_path}"', shell=True)


def valid_file_arg(obj, options):
    return bool([k for k in obj if k in options])


def main(*argv):
    parser = argument_parser(*argv)
    args = parser.parse_args()
    action = args.action[0]
    file = args.file
    path = args.path
    obj = base.parse_obj(file)
    cachedir = os.path.join(path, ".cache")
    options = ("blacklist", "ignore", "pack")
    if valid_file_arg(obj, options):
        if action == "add":
            add_entry(cachedir, obj)
        elif action == "view":
            view_entries(cachedir, obj)
        elif action == "edit":
            edit_file(cachedir, obj)
    else:
        base.Print.color(
            "file argument must include one of the following:", color=1
        )
        base.Print.color("- " + "\n- ".join(options), color=6)
        parser.print_help()
