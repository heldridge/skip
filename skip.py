import argparse
import os
import pathlib
import pkgutil
from typing import Dict

import frontmatter
import jinja2
import markdown
import watchgod

import server

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
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))

    if USE_DATA_DIR:
        data = process_datafiles()
    else:
        data = {}

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

        for filename in files:
            filepath = os.path.join(root, filename)
            if filename.endswith(".md"):
                with open(filepath) as infile:
                    file_frontmatter = frontmatter.load(infile)

                filedir = site_dir / root / filename[:-3]
                os.makedirs(filedir, exist_ok=True)
                page_path = filedir / "index.html"

                html = markdown.markdown(file_frontmatter.content)
                if "layout" in file_frontmatter:
                    template = jinja_env.get_template(file_frontmatter["layout"])
                    html = template.render(content=html, data=data)

                print("Writing", page_path, "from", filepath)
                with open(page_path, "w+") as outfile:
                    outfile.write(html)
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
    args = parser.parse_args()

    build_site()

    if args.serve:
        server.run("_site", args.port)

    if args.watch or args.serve:
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
