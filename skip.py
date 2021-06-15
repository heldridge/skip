import pkgutil

import _data

if __name__ == "__main__":

    data_modules = []
    for loader, module_name, is_pkg in pkgutil.iter_modules(_data.__path__):
        module = loader.find_module(module_name).load_module(module_name)
        data_modules.append(module)

    for module in data_modules:
        print(module.get_data())
