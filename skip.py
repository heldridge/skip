import argparse
import os
import pathlib
import pkgutil
from typing import Dict

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
    import config
except ImportError:
    print("No config found, using defaults")


def chunks(lst, n):
    """Yield successive n-sized chunks from lst

    Thank you SO: https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """

    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def process_datafiles() -> Dict:
    data_map = {}
    for loader, module_name, is_pkg in pkgutil.iter_modules(data.__path__):
        module = loader.find_module(module_name).load_module(module_name)
        data_map[module_name] = module.get_data()

    return data_map


def write_page(page_dir, filepath, html):
    page_path = page_dir / "index.html"
    print("Writing", page_path, "from", filepath)
    os.makedirs(page_dir, exist_ok=True)
    with open(page_path, "w+") as outfile:
        outfile.write(html)


def build_site(site_dir_name, should_ignore):
    print("Building Site")
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))

    if USE_DATA_DIR:
        data = process_datafiles()
    else:
        data = {}

    site_dir = pathlib.Path(site_dir_name)
    os.makedirs(site_dir, exist_ok=True)

    ignore_dirs = {".git", "data", site_dir_name, "templates", "__pycache__"}
    for root, dirs, files in os.walk("."):
        # Prune directories we don't want to visit
        del_indexes = []
        for index, dirname in enumerate(dirs):
            if dirname in ignore_dirs or should_ignore(os.path.join(root, dirname)):
                del_indexes.append(index)
        for index in sorted(del_indexes, reverse=True):
            del dirs[index]

        for filename in files:
            filepath = os.path.join(root, filename)

            suffix = pathlib.Path(filename).suffix

            if suffix in {".md", ".j2", ".html"}:
                with open(filepath) as infile:
                    file_frontmatter = frontmatter.load(infile)

                page_dir = site_dir / root / filename[:-3]

                if suffix == ".html":
                    html = file_frontmatter.content
                elif suffix == ".md":
                    html = markdown.markdown(file_frontmatter.content)
                    if "layout" in file_frontmatter:
                        template = jinja_env.get_template(file_frontmatter["layout"])
                        html = template.render(
                            content=html, data=data, **file_frontmatter
                        )
                elif suffix == ".j2":
                    template = jinja2.Template(file_frontmatter.content)

                    if "pagination" in file_frontmatter:
                        pagination_data = data[file_frontmatter["pagination"]["data"]]
                        page_size = file_frontmatter["pagination"]["size"]

                        for index, page in enumerate(
                            chunks(pagination_data, page_size)
                        ):
                            html = template.render(
                                data=data, page=page, **file_frontmatter
                            )
                            if index != 0:
                                new_page_dir = page_dir / str(index)
                            else:
                                new_page_dir = page_dir
                            write_page(new_page_dir, filepath, html)

                        continue
                    else:
                        html = template.render(data=data, **file_frontmatter)

                write_page(page_dir, filepath, html)

    print("Build Complete!\n")


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
        default="_site",
    )
    args = parser.parse_args()

    skipignore_path = pathlib.Path(".skipignore")
    if skipignore_path.exists():
        print("Using .skipignore...")
        should_ignore = parse_gitignore(skipignore_path)
    else:
        print("No .skipignore found, using defaults...")
        should_ignore = lambda _: False

    build_site(args.output, should_ignore)

    if args.serve:
        server.run(args.output, args.port)

    if args.watch or args.serve:
        print("\nWatching files for changes...")

        if should_ignore is not None:
            for changes in watchgod.watch(
                ".",
                watcher_cls=watchers.SkipIgnoreWatcher,
                watcher_kwargs={"should_ignore": should_ignore},
            ):
                build_site(args.output, should_ignore)
        else:
            for changes in watchgod.watch(".", watcher_cls=watchers.SkipDefaultWatcher):
                build_site(args.output, should_ignore)


if __name__ == "__main__":
    main()
