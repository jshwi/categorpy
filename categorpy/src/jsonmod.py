import argparse
import json
import os

from . import base


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


def subconditions(obj, categorized):
    if isinstance(obj, dict):
        categorized = recurse_categorized(obj, categorized)
    elif isinstance(obj, list):
        categorized = recurse_categorized(obj, categorized)
    else:
        categorized.append(obj)
    return categorized


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


def remove_ignored(uncategorized):
    ignore_files = (base.IGNORE, base.BLACKLIST, base.PACK)
    return [i for i in uncategorized if i not in ignore_files]


def parse_into_json(ignore_file, uncategorized, obj, dead_links, parent):
    if os.path.isfile(ignore_file):
        ignore_list = base.parse_file(ignore_file)
        uncategorized = base.filter_list(uncategorized, ignore_list)
    uncategorized = remove_ignored(uncategorized)
    if uncategorized:
        obj[parent].update({"Uncategorized": uncategorized})
    if dead_links:
        obj[parent].update({"Dead-Link": dead_links})
    if base.CACHE in obj[parent]:
        del obj[parent][base.CACHE]
    return json.dumps(obj, indent=4, sort_keys=True)


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
            cache = json.load(json_file)
        return cache
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
        cache = read_cache(index)
        deleted = compare_cache(cache, session)
        assume_blacklisted(path, deleted)
    else:
        os.mkdir(cachedir)
    write_cache(index, session)


def main(*argv):
    args = argument_parser(*argv)
    path = args.path
    cache_run = args.cache
    ignore_file = os.path.join(path, base.IGNORE)
    parent = os.path.basename(path)
    obj = base.get_object(path, parent)
    paths = base.get_index(path, os.path.join(path, base.IGNORE))
    cacher(path, paths, parent)
    if not cache_run:
        uncategorized, dead_links = base.get_uncategorized(obj, paths, path)
        result = parse_into_json(
            ignore_file, uncategorized, obj, dead_links, parent
        )
        print(result)
