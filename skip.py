import asyncio
import pkgutil
from typing import Dict

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


async def main():
    async for changes in awatch("."):
        build_site()


if __name__ == "__main__":
    build_site()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
