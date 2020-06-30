import argparse
import json
import os

from . import base, cache


def argument_parser(*_):
    module = base.Print.get_color("categorpy[json]", color=6)
    parser = argparse.ArgumentParser(prog=module)
    parser.add_argument(
        "path",
        action="store",
        help="fullpath to directory you wish to analyze",
    )
    parser.add_argument(
        "-c",
        "--cache",
        action="store_true",
        help="only run the cache process",
    )
    _args = parser.parse_args()
    return _args


def cache_index(paths):
    obj = {"file": [], "symlink": []}
    for file in paths:
        if os.path.islink(file):
            obj["symlink"].append(file)
        else:
            obj["file"].append(file)
    return obj


def write_cache(index, obj):
    with open(index, "w") as json_file:
        json_file.write(json.dumps(obj, indent=4))


def read_cache(index):
    try:
        with open(index) as json_file:
            _cache = json.load(json_file)
        return _cache
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        return {"file": [], "symlink": []}


def compare_cache(saved, session):
    return [s for s in saved["file"] if s not in session["file"]]


def assume_blacklisted(path, deleted):
    blacklist = os.path.join(path, base.BLACKLIST)
    with open(blacklist, "a") as blacklisted:
        for file in deleted:
            blacklisted.write(f"{os.path.basename(file)}\n")


def cacher(path, paths, parent):
    cachedir = os.path.join(path, base.CACHE)
    index = os.path.join(cachedir, parent)
    session = cache_index(paths)
    if os.path.isdir(cachedir):
        _cache = read_cache(index)
        deleted = compare_cache(_cache, session)
        assume_blacklisted(path, deleted)
    else:
        os.mkdir(cachedir)
    write_cache(index, session)


def main(*argv):
    args = argument_parser(*argv)
    path = args.path
    paths = base.get_index(path)
    parent = os.path.basename(path)
    _cacher = cache.Cacher(path, paths, parent)
    _cacher.cacher()
    if not cache:
        obj = base.get_object(path, parent)
        uncategorized, deadlink = base.get_uncategorized(obj, paths, path)
        json_parse = cache.JSONParse(uncategorized, obj, deadlink)
        result = json_parse.parse(parent)
        print(result)
