import argparse
import os

from . import base


def argument_parser(*_):
    module = base.Print.get_color("categorpy[report]", color=6)
    parser = argparse.ArgumentParser(prog=module)
    parser.add_argument(
        "path",
        action="store",
        help="fullpath to directory you wish to analyze",
    )
    _args = parser.parse_args()
    return _args


class ParseReport:
    def __init__(self, paths, root):
        self.paths = [p for p in paths if os.path.basename(p) != base.IGNORE]
        self.root = root
        self.accumulate = 0
        self.tab = len(max(self.paths, key=len))
        self.filebullet, self.symbullet, self.dirbullet = self._bullet(
            "FILE", "DEADLINK", "FOLDER"
        )
        self.bulletlen = len(self.symbullet)
        self.colors = {"b": 2, "f": 0, "s": 6}

    def _separator(self, vartext, symbol, color):
        return base.Print.get_color(
            f"{(self.tab + self.bulletlen + 12 + len(vartext)) * symbol}\n",
            color=color,
            bold=True,
        )

    def _container(self, info, vartext, color, **kwargs):
        if "top" not in kwargs or "bot" not in kwargs:
            val = kwargs["top"] if kwargs["top"] else kwargs["bot"]
            top = bot = val if val else "="
        else:
            top, bot = kwargs["top"], kwargs["bot"]
        top_sep = self._separator(vartext, top, color)
        bot_sep = self._separator(vartext, bot, color)
        return f"{top_sep}{info}{bot_sep}"

    @staticmethod
    def _bullet(*args):
        decorated = []
        for arg in args:
            try:
                whitespace = (
                    round(round(len(max(args, key=len)) - len(arg)) / 2) * " "
                )
            except ValueError:
                whitespace = ""
            decorated.append(f"[{whitespace}{arg}{whitespace}]: ")
        return decorated

    def _header(self, hstr, sstr, color=2):
        tab = self.dynamic_tab(hstr)
        header = base.Print.get_color(f"{hstr}{tab}", color=color, bold=True)
        pipe = "| "
        stats = base.Print.get_color(f"{sstr}\n", color=color, bold=True)
        return f"{header}{pipe}{stats}"

    def _set_types(self, fullpath):
        if os.path.islink(fullpath):
            bullet = self.symbullet
            self.colors.update({"b": 1, "f": 1, "s": 1})
        else:
            bullet = self.filebullet
            self.colors.update({"b": 2, "f": 0, "s": 6})
        return bullet

    @staticmethod
    def byte_prefix(size):
        prefixes = {
            "B  ": 1024,  # how many can be held before progressing
            "KiB": 1048576,
            "MiB": 1073741824,
            "GiB": 1099511627776,
            "TiB": 1125899906842624,
        }
        adjusted = size
        for key, val in prefixes.items():
            try:
                if size > val:
                    adjusted = size / val
                else:
                    return f"{key} {round(adjusted, 1)}"
            except ZeroDivisionError:
                continue
        return None

    def _get_sint(self, sint):
        size = self.byte_prefix(sint)
        return base.Print.get_color(size, color=self.colors["s"])

    def _get_fstr(self, file):
        if self.colors["f"]:
            return base.Print.get_color(file, color=self.colors["f"])
        return file

    @staticmethod
    def _safe_getsize(path):
        try:
            return os.path.getsize(path)
        except FileNotFoundError:
            return 0

    def _get_file(self, fstr):
        fullpath = os.path.join(self.root, fstr)
        bstr = self._set_types(fullpath)
        sint = self._safe_getsize(fullpath)
        self.accumulate += sint
        dyn_tab = (self.tab - len(fstr) + 4) * " "
        bullet = base.Print.get_color(bstr, color=self.colors["b"])
        file = self._get_fstr(fstr)
        size = self._get_sint(sint)
        return f"{bullet}{file}{dyn_tab}| {size}\n"

    def dynamic_tab(self, adjust_for_str):
        return (self.tab + self.bulletlen + 4 - len(adjust_for_str)) * " "

    def total_dir_size(self):
        total = 0
        path_list = base.get_index(
            self.root, os.path.join(self.root, ".ignore")
        )
        for path in path_list:
            total += self._safe_getsize(path)
        return total

    def parse_report(self):
        filetxt = "Files"
        header = self._header(filetxt, "Size")
        str_ = self._container(header, filetxt, 4, top="=", bot="-")
        hstr = f"{self.dirbullet}{self.root}{os.sep}"
        sint = self.total_dir_size()
        size = self.byte_prefix(sint)
        header = self._header(hstr, size)
        str_ += self._container(header, filetxt, 5, top="-")
        for file in self.paths:
            str_ += self._get_file(file)
        announce = "Total uncategorized file usage:"
        subtotal = self.byte_prefix(self.accumulate)
        header = self._header(announce, subtotal)
        str_ += self._container(header, filetxt, 4, top="-", bot="=")
        str_ += base.Print.get_color(
            f"{round(sint/self.accumulate, 2)}% of directory is uncategorized"
        )
        return str_


def main(*argv):
    report = True
    args = argument_parser(*argv)
    path = args.path
    parent = os.path.basename(path)
    obj = base.get_object(path, parent)
    paths = base.get_index(path, os.path.join(path, base.IGNORE))
    uncategorized, dead_links = base.get_uncategorized(
        obj, paths, path, report
    )
    sort_view = sorted(uncategorized + dead_links)
    parser = ParseReport(sort_view, path)
    result = parser.parse_report()
    print(result)
