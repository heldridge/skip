import argparse
from collections import defaultdict
import errno
import os
from pathlib import Path
import pkgutil
import shutil
from typing import Any, Callable, List, Mapping

from gitignore_parser import parse_gitignore
import jinja2
import watchgod

import server
from sources import DataFile, DataFileFactory, PageFile, PageFileFactory, SitePage
import watchers


USE_DATA_DIR = True
try:
    import data
except ImportError:
    USE_DATA_DIR = False

try:
    import settings
except ImportError:
    print("No settings file found, using defaults")
    USE_SETTINGS = False


class NonDictDataFileException(Exception):
    pass


def process_datafiles() -> dict:
    data_map = {}
    for loader, module_name, is_pkg in pkgutil.iter_modules(data.__path__):
        module = loader.find_module(module_name).load_module(module_name)
        data_map[module_name] = module.get_data()

    return data_map


def write_page(
    site_dir: Path, permalink: Path, filepath: Path, html: str, quiet: bool = False
) -> None:
    full_path = site_dir / permalink
    if not quiet:
        print("Writing", full_path, "from", filepath)
    os.makedirs(full_path.parent, exist_ok=True)
    with open(full_path, "w+") as outfile:
        outfile.write(html)


def get_page_files(
    ignores: set[str], should_ignore: Callable[[str], bool], path: Path, data: dict
) -> List[PageFile]:
    page_paths = []
    page_files: List[PageFile] = []
    data_files: List[DataFile] = []
    dirs = []

    pff = PageFileFactory()
    dff = DataFileFactory()
    # Go over all the files to identiy all the data and page sources
    for entry in os.scandir(path):
        if entry.name in ignores or should_ignore(entry.path):
            continue
        if entry.is_dir():
            dirs.append(Path(entry.path))
        elif entry.is_file():
            path = Path(entry.path)
            if pff.is_valid_file(path):
                # Don't load pages yet because we need to process all the data first
                page_paths.append(path)
            elif dff.is_valid_file(path):
                data_files.append(dff.load_source_file(path))

    for data_file in data_files:
        file_data = data_file.get_data()

        if not isinstance(file_data, dict):
            raise NonDictDataFileException(
                "Non-global data files must return dictionaries"
            )
        data = {**data, **data_file.get_data()}

    for page_path in page_paths:
        page_files.append(pff.load_source_file(page_path, data))

    # Recurse
    for dir_path in dirs:
        page_files += get_page_files(ignores, should_ignore, dir_path, data)

    return page_files


def get_collections(pages: List[PageFile]) -> Mapping[str, List[PageFile]]:
    collections = defaultdict(list)
    for page in pages:
        for tag in page.tags:
            collections[tag].append(page)

    return collections


def false(_: Any) -> bool:
    return False


def build_site(config: dict, should_ignore: Callable[[str], bool]) -> None:
    print("Building Site")

    if USE_DATA_DIR:
        data = process_datafiles()
    else:
        data = {}

    site_dir = Path(config["output"])

    ignore_dirs = {".git", "data", config["output"], "templates", "__pycache__"}
    page_files = get_page_files(ignore_dirs, should_ignore, Path("."), data)
    collections = get_collections(page_files)

    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))
    for page_file in page_files:
        pages = page_file.get_pages(collections)
        for page in pages:
            html = page.render(jinja_env)
            write_page(site_dir, page.get_permalink(), page.source.path, html)

    for copy_target in config["copy"]:
        if ":" in copy_target:
            src, dest = copy_target.split(":")
        else:
            src = dest = copy_target

        dest = site_dir / dest
        print(f"Copying {src} to {dest}")

        try:
            shutil.copytree(src, dest, dirs_exist_ok=True)
        except OSError as e:
            if e.errno == errno.ENOTDIR:
                shutil.copy(src, dest)
            else:
                raise e

    print("Build Complete!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w", "--watch", help="Watch files and reload on changes", action="store_true"
    )
    parser.add_argument(
        "-s", "--serve", help="Serve the site on localhost", action="store_true"
    )
    parser.add_argument("-p", "--port", help="The port to serve on", type=int)
    parser.add_argument(
        "-o",
        "--output",
        help="The directory to output the built site to",
    )
    parser.add_argument(
        "-c",
        "--copy",
        help=(
            "Files or directories to copy into the root of site folder. Use a colon to "
            'specify a new path. For example, "x.css:style/x.css" will copy the file '
            'to "./_site/style/x.css"'
        ),
        nargs="+",
    )
    args = parser.parse_args()

    skipignore_path = Path(".skipignore")
    if skipignore_path.exists():
        print("Using .skipignore...")
        should_ignore = parse_gitignore(skipignore_path)
    else:
        print("No .skipignore found, using defaults...")
        should_ignore = false

    # Default config
    config = {"output": "_site", "copy": []}

    if settings:
        config = {**config, **vars(settings).get("OPTIONS", {})}

    # CLI flags take precedence over settings file
    dict_args = vars(args)
    arg_config_options = ["output", "port", "copy"]
    for option in arg_config_options:
        if dict_args[option] is not None:
            config[option] = dict_args[option]

    build_site(config, should_ignore)

    if args.serve:
        server.run(config)

    if args.watch or args.serve:
        print("\nWatching files for changes...")

        if should_ignore is not None:
            for changes in watchgod.watch(
                ".",
                watcher_cls=watchers.SkipIgnoreWatcher,
                watcher_kwargs={"should_ignore": should_ignore},
            ):
                build_site(config, should_ignore)
        else:
            for changes in watchgod.watch(".", watcher_cls=watchers.SkipDefaultWatcher):
                build_site(config, should_ignore)


if __name__ == "__main__":
    main()
