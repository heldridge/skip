import argparse
from collections import defaultdict
import enum
import errno
import json
import os
from pathlib import Path
import pkgutil
import shutil
import sys
from typing import Any, Callable, Generator, List, Mapping

import frontmatter
from gitignore_parser import parse_gitignore
import jinja2
import markdown
import watchgod

import server
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


def chunks(lst: List, n: int) -> Generator[List, None, None]:
    """Yield successive n-sized chunks from lst

    Thank you SO: https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """

    for i in range(0, len(lst), n):
        yield lst[i : i + n]


class FileType(enum.Enum):
    HTML = 0
    JINJA2 = 1
    MARKDOWN = 2
    JSON = 3
    PYTHON = 4


class SourceFile:
    SUFFIX_TO_TYPE = {
        ".html": FileType.HTML,
        ".j2": FileType.JINJA2,
        ".md": FileType.MARKDOWN,
        ".json": FileType.JSON,
        ".py": FileType.PYTHON,
    }

    def __init__(self, path: Path) -> None:
        self.path = path
        self.type = self.SUFFIX_TO_TYPE[self.path.suffix]

    def __str__(self) -> str:
        return str(self.path)


class PageFile(SourceFile):
    pass


class UnimplementedDataFileTypeException(Exception):
    pass


class DataFile(SourceFile):
    def get_data(self) -> dict:
        if self.type == FileType.JSON:
            with open(self.path) as infile:
                return json.load(infile)
        elif self.type == FileType.PYTHON:
            parent_path = str(self.path.parent)
            if self.path.parent.name != "":
                sys.path.append(parent_path)
                module = __import__(self.path.stem)

                data = module.get_data()

                sys.path.remove(parent_path)

            return data
        else:
            raise UnimplementedDataFileTypeException(self.type)


class SitePage:
    def __init__(self, source: PageFile, data: dict) -> None:
        self.source = source
        self.data = data

        with open(self.source.path) as infile:
            metadata, self.content = frontmatter.parse(infile.read())

        self.data = {**self.data, **metadata}

    def render(
        self,
        site_dir: Path,
        jinja_env: jinja2.Environment,
        collections: Mapping[str, List["SitePage"]],
    ) -> None:

        page_dir = site_dir / self.source.path.stem

        if self.source.type == FileType.HTML:
            html = self.content
        elif self.source.type == FileType.MARKDOWN:
            html = markdown.markdown(self.content)
            if "layout" in self.data:
                template = jinja_env.get_template(self.data["layout"])
                html = template.render(
                    content=html, data=self.data, collections=collections
                )
        elif self.source.type == FileType.JINJA2:
            template = jinja2.Template(self.content)

            if "pagination" in self.data:
                pagination_source = self.data["pagination"]["data"]

                if pagination_source in self.data:
                    pagination_data = self.data[pagination_source]
                elif pagination_source in collections:
                    pagination_data = collections[pagination_source]
                else:
                    print(
                        f"Warning: pagination source {pagination_source} not found for "
                        f"{self.source}"
                    )
                    pagination_data = []

                for index, items in enumerate(
                    chunks(pagination_data, self.data["pagination"]["size"])
                ):
                    html = template.render(
                        data=self.data, items=items, collections=collections
                    )
                    if index == 0:
                        new_page_dir = page_dir
                    else:
                        new_page_dir = page_dir / str(index)
                    write_page(new_page_dir, self.source.path, html)

                return

            else:
                html = template.render(data=self.data, collections=collections)

        write_page(page_dir, self.source.path, html)


def process_datafiles() -> dict:
    data_map = {}
    for loader, module_name, is_pkg in pkgutil.iter_modules(data.__path__):
        module = loader.find_module(module_name).load_module(module_name)
        data_map[module_name] = module.get_data()

    return data_map


def write_page(page_dir: Path, filepath: Path, html: str) -> None:
    page_path = page_dir / "index.html"
    print("Writing", page_path, "from", filepath)
    os.makedirs(page_dir, exist_ok=True)
    with open(page_path, "w+") as outfile:
        outfile.write(html)


def load_site_file(
    entry: os.DirEntry, page_files: List[PageFile], data_files: List[DataFile]
) -> tuple[List[PageFile], List[DataFile]]:
    entry_path = Path(entry.path)
    suffix = entry_path.suffix

    if suffix in {".html", ".j2", ".md"}:
        return page_files + [PageFile(entry_path)], data_files
    elif suffix in {".json"} or (
        entry_path.suffixes == [".skipdata", ".py"]
        and entry_path.parent.name
        != ""  # Ignore python files in the top level directory
    ):
        return page_files, data_files + [DataFile(entry_path)]
    else:
        return page_files, data_files


def get_pages(
    ignores: set[str], should_ignore: Callable[[str], bool], path: Path, data: dict
) -> List[SitePage]:
    pages = []
    page_files: List[PageFile] = []
    data_files: List[DataFile] = []
    dirs = []

    # Go over all the files to identiy all the data and page sources
    for entry in os.scandir(path):
        if entry.name in ignores or should_ignore(entry.path):
            continue
        if entry.is_dir():
            dirs.append(Path(entry.path))
        elif entry.is_file():
            page_files, data_files = load_site_file(entry, page_files, data_files)

    for data_file in data_files:
        data = {**data, **data_file.get_data()}

    for page_file in page_files:
        pages.append(SitePage(page_file, data))

    # Recurse
    for dir_path in dirs:
        pages += get_pages(ignores, should_ignore, dir_path, data)

    return pages


def get_collections(pages: List[SitePage]) -> Mapping[str, List[SitePage]]:
    collections = defaultdict(list)
    for page in pages:
        if "tags" in page.data:
            tags = page.data["tags"]
            if isinstance(tags, str):
                collections[tags].append(page)
            elif isinstance(tags, list):
                for tag in tags:
                    collections[tag].append(page)
    return collections


def false(_: Any) -> bool:
    return False


def build_site(config: dict, should_ignore: Callable[[str], bool]) -> None:
    print("Building Site")
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))

    if USE_DATA_DIR:
        data = process_datafiles()
    else:
        data = {}

    site_dir = Path(config["output"])
    os.makedirs(site_dir, exist_ok=True)

    ignore_dirs = {".git", "data", config["output"], "templates", "__pycache__"}
    pages = get_pages(ignore_dirs, should_ignore, Path("."), data)
    collections = get_collections(pages)

    for page in pages:
        page.render(site_dir, jinja_env, collections)

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
