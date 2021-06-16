import os
import pathlib
import pkgutil
from typing import Dict

import markdown
import watchgod

USE_DATA_DIR = True
try:
    import _data
except ImportError:
    USE_DATA_DIR = False


def process_datafiles() -> Dict:
    data = {}
    for loader, module_name, is_pkg in pkgutil.iter_modules(_data.__path__):
        module = loader.find_module(module_name).load_module(module_name)
        data[module_name] = module.get_data()

    return data


def build_site():
    if USE_DATA_DIR:
        data = process_datafiles()
        print(data)

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
            if file.endswith(".md"):
                with open(os.path.join(root, file)) as infile:
                    md = infile.read()

                filename = file[:-3]
                filedir = site_dir / root / filename
                os.makedirs(filedir, exist_ok=True)
                page_path = filedir / "index.html"

                print("Writing", page_path, "from", file)
                with open(page_path, "w+") as outfile:
                    outfile.write(markdown.markdown(md))


def main():
    build_site()
    # Ignore changes in files or directories that start with "_" or "."
    for changes in watchgod.watch(
        ".", watcher_cls=watchgod.RegExpWatcher, watcher_kwargs={"re_dirs": "^[^_.]*$"}
    ):
        build_site()


if __name__ == "__main__":
    main()
