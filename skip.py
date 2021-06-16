import argparse
import os
import pathlib
import pkgutil
from typing import Dict

import markdown
import watchgod

USE_DATA_DIR = True
try:
    import data
except ImportError:
    USE_DATA_DIR = False


def process_datafiles() -> Dict:
    data_map = {}
    for loader, module_name, is_pkg in pkgutil.iter_modules(data.__path__):
        module = loader.find_module(module_name).load_module(module_name)
        data_map[module_name] = module.get_data()

    return data_map


def build_site():
    print("Building Site")
    if USE_DATA_DIR:
        data = process_datafiles()

    site_dir = pathlib.Path("_site")
    os.makedirs(site_dir, exist_ok=True)

    ignore_dirs = {".git", "data", "_site", "__pycache__"}
    for root, dirs, files in os.walk("."):
        # Prune directories we don't want to visit
        del_indexes = []
        for index, dirname in enumerate(dirs):
            if dirname in ignore_dirs:
                del_indexes.append(index)
        for index in sorted(del_indexes, reverse=True):
            del dirs[index]

        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith(".md"):
                with open(filepath) as infile:
                    md = infile.read()

                filename = file[:-3]
                filedir = site_dir / root / filename
                os.makedirs(filedir, exist_ok=True)
                page_path = filedir / "index.html"

                print("Writing", page_path, "from", filepath)
                with open(page_path, "w+") as outfile:
                    outfile.write(markdown.markdown(md))
    print("Build Complete!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w", "--watch", help="Watch files and reload on changes", action="store_true"
    )

    args = parser.parse_args()

    build_site()

    if args.watch:
        print("\nWatching files for changes...")
        # Ignore changes in files or directories that start with "_" or "."
        for changes in watchgod.watch(
            ".",
            watcher_cls=watchgod.RegExpWatcher,
            watcher_kwargs={"re_dirs": "^[^_.]*$"},
        ):
            build_site()
            print("")


if __name__ == "__main__":
    main()
