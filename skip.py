import asyncio
import pkgutil

from watchgod import awatch

import _data


def process_data():
    data_modules = []
    for loader, module_name, is_pkg in pkgutil.iter_modules(_data.__path__):
        module = loader.find_module(module_name).load_module(module_name)
        data_modules.append(module)

    for module in data_modules:
        print(module.get_data())


async def main():
    async for changes in awatch("_data"):
        process_data()


if __name__ == "__main__":
    process_data()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
