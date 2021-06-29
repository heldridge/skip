import json
from pathlib import Path
import sys
from typing import Any, Generator, Union

import frontmatter
import jinja2


def chunks(lst: list, n: int) -> Generator[list, None, None]:
    """Yield successive n-sized chunks from lst

    Thank you SO: https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """

    for i in range(0, len(lst), n):
        yield lst[i : i + n]


class SitePage:
    def __init__(
        self, source: "PageFile", data: dict, collections: dict[str, list["PageFile"]]
    ) -> None:
        self.source = source
        self.data = data
        self.collections = collections

    def render(self, jinja2_env: jinja2.Environment) -> str:
        template = jinja2_env.from_string(self.source.content)
        return template.render(data=self.data, collections=self.collections)


class PaginationSitePage(SitePage):
    def __init__(
        self,
        source: "PageFile",
        data: dict,
        collections: dict[str, list["PageFile"]],
        index: int,
        items: list,
    ) -> None:
        super().__init__(source, data, collections)
        self.index = index
        self.items = items

    def render(self, jinja2_env: jinja2.Environment) -> str:
        template = jinja2_env.from_string(self.source.content)
        return template.render(
            data=self.data, collections=self.collections, items=self.items
        )


class InvalidFileExtensionException(Exception):
    pass


class InvalidTagsException(Exception):
    pass


class MissingPaginationSourceException(Exception):
    pass


class SourceFile:
    suffixes: set

    def __init__(self, path: Path) -> None:
        if path.suffix not in self.suffixes:
            raise InvalidFileExtensionException(path.suffix)
        self.path = path

    def __str__(self):
        return str(self.path)


class PageFile(SourceFile):
    def __init__(self, path: Path, data: dict) -> None:
        super().__init__(path)

        with open(self.path) as infile:
            metadata, self.content = frontmatter.parse(infile.read())

        self.data = {**data, **metadata}

        if "tags" in self.data:
            if isinstance(self.data["tags"], str):
                self.tags = set()
                self.tags.add(self.data["tags"])
            elif isinstance(self.data["tags"], list):
                self.tags = set(self.data["tags"])
            else:
                raise InvalidTagsException(
                    f"Invalid tags for file at {self.path}. Expected <str> or <list>, "
                    f"got {type(self.data['tags'])}"
                )
        else:
            self.tags = []

    def get_pages(self, collections: dict[str, list["PageFile"]]) -> list[SitePage]:
        if "pagination" in self.data:

            pagination_source = self.data["pagination"]["data"]

            if pagination_source in self.data:
                pagination_data = self.data[pagination_source]
            elif pagination_source in collections:
                pagination_data = collections[pagination_source]
            else:
                raise MissingPaginationSourceException(pagination_source)

            pages = []
            for index, items in enumerate(
                chunks(pagination_data, self.data["pagination"]["size"])
            ):
                pages.append(
                    PaginationSitePage(self, self.data, collections, index, items)
                )
            return pages
        else:
            return [SitePage(self, self.data, collections)]


class MarkdownFile(PageFile):
    suffixes = {".md"}


class Jinja2File(PageFile):
    suffixes = {".html", ".j2"}


class DataFile(SourceFile):
    def get_data(self):
        return None


class JSONFile(DataFile):
    suffixes = {".json"}

    def get_data(self) -> Union[list, dict]:
        with open(self.path) as infile:
            return json.load(infile)


class PythonFile(DataFile):
    suffixes = {".py"}

    def get_data(self) -> Any:
        parent_path = str(self.path.parent)
        if self.path.parent.name != "":
            sys.path.append(parent_path)
            module = __import__(self.path.stem)
            data = module.get_data()
            sys.path.remove(parent_path)

            return data


class DataFileFactory:
    suffix_to_class_map = {".json": JSONFile, ".py": PythonFile}

    def is_valid_file(self, path: Path) -> bool:
        return path.suffix in self.suffix_to_class_map and (
            path.suffix != ".py" or path.parent.name != ""
        )

    def load_source_file(self, path: Path) -> DataFile:
        suffix = path.suffix
        if not self.is_valid_file(path):
            raise InvalidFileExtensionException(
                f"No DataFile type found with suffix {suffix}"
            )
        return self.suffix_to_class_map[suffix](path)


class PageFileFactory:
    suffix_to_class_map = {".html": Jinja2File, ".md": MarkdownFile, ".j2": Jinja2File}

    def is_valid_file(self, path: Path) -> bool:
        return path.suffix in self.suffix_to_class_map

    def load_source_file(self, path: Path, data: dict) -> DataFile:
        suffix = path.suffix
        if not self.is_valid_file(path):
            raise InvalidFileExtensionException(
                f"No PageFile type found with suffix {suffix}"
            )

        return self.suffix_to_class_map[suffix](path, data)
