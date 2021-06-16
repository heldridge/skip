import asyncio
import os
import pathlib
import pkgutil
from typing import Dict

import markdown
from watchgod import awatch

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

    for file in os.listdir("."):
        if file.endswith(".md"):
            print("Processing:", file)
            with open(file) as infile:
                md = infile.read()

            filename = file[:-3]
            os.makedirs(site_dir / filename)

            page_path = site_dir / filename / "index.html"

            print("Writing", page_path, "from", file)
            with open(page_path, "w+") as outfile:
                outfile.write(markdown.markdown(md))


async def main():
    async for changes in awatch("."):
        build_site()


if __name__ == "__main__":
    build_site()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
