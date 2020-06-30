import datetime
import os
from urllib.request import Request, urlopen

import bs4
from appdirs import user_cache_dir, user_data_dir

CACHE = ".cache"
APPNAME = "categorpy"
CACHEDIR = user_cache_dir(APPNAME)
DATADIR = user_data_dir(APPNAME)
LOGDIR = os.path.join(CACHEDIR, "log")
BLACKLIST = os.path.join(DATADIR, "blacklist")
IGNORE = os.path.join(DATADIR, "ignore")
PACK = os.path.join(DATADIR, "pack")
HTTP = os.path.join(DATADIR, "http")
DATE = datetime.date.today().strftime("%Y%m%d")
TIME = datetime.datetime.now().strftime("%H:%M:%S")


class Print:
    """Print to stdout, stderr and print in color or no color"""

    @staticmethod
    def _hack_newlines(args):
        # to split, and retain the newline, add a newline for every
        # newline that is not at the beginning of the string
        # (splitlines will retain this one)
        # because splitlines will split at the newline if there are
        # multiple newlines there will be the split and the remaining
        # new line, meaning this will actually be retained
        # so revert thee newlines back to two to return a double newline
        # we won't be using three newlines so it does not need to carry
        # on
        lines = list(args)
        for count, line in enumerate(lines):
            prepend = ""
            if line != "" and line[0] == "\n":
                prepend, line = "\n", line[1:]
            line = line.replace("\n", "\n\n")
            line = line.replace("\n\n\n", "\n\n")
            lines[count] = prepend + line
        return lines

    @classmethod
    def _place_newlines(cls, *args):
        # place the newlines outside of the escape codes for the
        # beginning and ending of a string
        # This makes its a lot easier and more logical to write readable
        # tests when lines aren't being split through their ASCII escape
        # code pattern
        args = cls._hack_newlines(args)
        lines = "".join(args).splitlines()
        for count, line in enumerate(lines):
            if line == "":
                lines[count] = "\n"
        return lines

    @staticmethod
    def _color_strings(lines, color, bold):
        # apply the ASCII escape code to a string multiple times if
        # it contains a newline
        # each line will have a starting and stop ASCII code
        for count, line in enumerate(lines):
            if line != "\n":
                lines[count] = f"\u001b[{bold};3{color};40m{line}\u001b[0;0m"
        return lines

    @classmethod
    def get_color(cls, *args, **kwargs):
        """Returns a colored string, but does not print it

        :param args:    String(s) to be printed in color
        :key bold:      True or False: bool = False
        :key color:     Ascii color code: int = 3 (yellow)
        :returns:       String of selected color
        """
        bold = int(kwargs.get("bold", False))
        color = kwargs.get("color", 3)
        lines = cls._place_newlines(*args)
        colored = cls._color_strings(lines, color, bold)
        return "".join(colored)

    @classmethod
    def color(cls, *args, **kwargs):
        """Prints get_color() to stdout in the terminal

        :param args:    String(s) to be printed in color
        :key bold:      True or False: bool = False
        :key color:     Ascii color code: int = 3 (yellow)
        :returns:       String of selected color
        """
        bold = kwargs.get("bold", False)
        color = kwargs.get("color", 3)
        print(cls.get_color(*args, bold=bold, color=color))


class Walk:
    """Inherit this class to walk through the directory structure of
    user notebooks for various class related processes

    :param root:        The root directory which the class will walk
    :param method:      The method that the class inheriting this class
                        will pass to super
    :param args:        Directories that the inheriting class wants to
                        ignore
    """

    def __init__(self, root, method, *args):
        super().__init__()
        self._root = root
        self._method = method
        self._ignore = args

    def walk_files(self, root, files):
        """Walk through the notes directory structure and perform
        variable actions on directory files specifically

        :param root:    Top level of directory structure
        :param files:   List of files within directory structure
        """
        for file in files:
            fullpath = os.path.join(root, file)
            self._method(fullpath)

    def walk_dirs(self):
        """Iterate through walk if the root directory exists

        - Skip directories in list parameter and create fullpath
          with root and files
        - forget about the directories returned by walk
        - Once files are determined perform the required actions
        """
        if os.path.isdir(self._root):
            for root, _, files in os.walk(self._root):
                if self._ignore and root in self._ignore:
                    continue
                self.walk_files(root, files)


class IndexNotebook(Walk):
    """Get all the directories in the notebook repository as a list
    object of all absolute paths

    :param root:        The root directory which the class will walk
    :param args:        Directories that the inheriting class wants to
                        ignore
    """

    def __init__(self, root, *args):
        self.file_paths = []
        self._root = root
        super().__init__(root, self._get_list, *args)
        self._populate_list()

    def _populate_list(self):
        self.walk_dirs()

    def _get_list(self, file):
        # get list of files to display
        self.file_paths.append(file)
        self.file_paths = sorted(self.file_paths)


def parse_file(file):
    try:
        with open(file) as textio:
            list_ = textio.read().splitlines()
        return list_
    except FileNotFoundError:
        with open(file, "w") as _:
            # python version of shell's `touch`
            pass
        return []


def rm_dirnames(fullpath, dirname):
    """Remote prior directories to the notebook directory

    :param fullpath:    Path of the file / directory for which the
                        notes section and all prior will be removed
    :param dirname:     Section of the path to take out
    :return:            The edited path
    """
    return fullpath.replace(dirname, "")[1:]


def strip(item, report=False, dirname=None):
    return rm_dirnames(item, dirname) if report else os.path.basename(item)


def get_index(path, *ignore):
    ignore = list(ignore)
    ignore.extend([".cache", ".blacklist", ".ignore", ".pack"])
    index_files = IndexNotebook(path, *ignore)
    return index_files.file_paths


def filter_list(focus, unwanted, **kwargs):
    report = kwargs.get("report", False)
    dirname = kwargs.get("dirname", None)
    return [
        strip(x, report, dirname) for x in focus if strip(x) not in unwanted
    ]


def scraper(search, path):
    req = Request(search, headers={"User-Agent": "Mozilla/5.0"})
    webpage = urlopen(req).read()
    soup = bs4.BeautifulSoup(webpage, "html.parser")
    results = []
    for result in soup.find_all("a", "detLink"):
        tag = result.get("href")
        results.append(tag.split("/")[-1])
    with open(path, "w") as file:
        for result in results:
            file.write(f"{result.replace('_', ' ')}\n")


def get_uncategorized(obj, paths, dirname, report=False):
    categorized = []
    symlinks = []
    files = []
    org = recurse_categorized(obj, categorized)
    for file in paths:
        symlinks.append(file) if os.path.islink(file) else files.append(file)
    uncategorized = filter_list(files, org, report=report, dirname=dirname)
    dead_link = filter_list(symlinks, org, report=report, dirname=dirname)
    return uncategorized, dead_link


def get_object(path, parent):
    return recurse_json(path, {parent: {}}, parent, path)


def recurse_json(path, obj, parent, root):
    for basename in os.listdir(path):
        fullpath = os.path.join(path, basename)
        if os.path.isfile(fullpath):
            if root != path:
                obj[parent].append(basename)
        elif os.path.isdir(fullpath):
            subvals = recurse_json(fullpath, {basename: []}, basename, root)
            if root == path:
                for key, val in subvals.items():
                    obj[parent].update({key: val})
            else:
                obj[parent].append(subvals)
    return obj


def parse_sub_obj(arg):
    # Parse a key, value pair, separated by '='
    obj = {}
    items = arg.split("=")
    key = items[0].strip()
    if len(items) > 1:
        value = "=".join(items[1:])
        obj.update({key: value})
    else:
        obj.update({key: None})
    return obj


def parse_obj(items):
    # Parse a series of key-value pairs and return a dictionary
    obj = {}
    if items:
        for item in items:
            obj.update(parse_sub_obj(item))
    return obj


def recurse_categorized(obj, categorized):
    if isinstance(obj, dict):
        for key, val in obj.items():
            categorized = subconditions(val, categorized)
    elif isinstance(obj, list):
        for val in obj:
            categorized = subconditions(val, categorized)
    else:
        categorized.append(obj)
    return categorized


def subconditions(obj, categorized):
    if isinstance(obj, dict):
        categorized = recurse_categorized(obj, categorized)
    elif isinstance(obj, list):
        categorized = recurse_categorized(obj, categorized)
    else:
        categorized.append(obj)
    return categorized
