from abc import ABC, abstractmethod
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, Generator, List, Union

import arrow
import frontmatter
import jinja2
import markdown


def chunks(lst: List, n: int) -> Generator[List, None, None]:
    """Yield successive n-sized chunks from lst

    Thank you SO: https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """

    for i in range(0, len(lst), n):
        yield lst[i : i + n]


class SitePage:
    def __init__(
        self, source: "PageFile", data: Dict, collections: Dict[str, List["PageFile"]]
    ) -> None:
        self.source = source
        self.data = data
        self.collections = collections
        self.template_data = {"data": self.data, "collections": self.collections}

    def render(self, jinja2_env: jinja2.Environment) -> str:
        html = self.source.get_html(jinja2_env, page=self, **self.template_data)
        if "layout" in self.data:
            template = jinja2_env.get_template(self.data["layout"])
            return template.render(
                content=html,
                page=self,
                data=self.data,
                collections=self.collections,
            )
        else:
            return html

    def get_path(self) -> Path:
        if "permalink" in self.data:

            jinja2_env = jinja2.Environment()

            permalink_template = jinja2_env.from_string(self.data["permalink"])
            permalink = permalink_template.render(data=self.data)
            if permalink.endswith("/"):
                # Filename is not specified, so append 'index.html'
                return Path(permalink) / "index.html"
            else:
                # Assume the last part of the path is the filename
                return Path(permalink)
        else:
            path = self.source.path
            if len(path.parts) == 1 and path.stem == "index":
                # Anything just named "index" in the top level dir becomes the
                # index page
                return Path("index.html")
            else:
                return path.parent / path.stem / "index.html"

    def get_permalink(self) -> str:
        permalink = str(self.get_path())

        if not permalink.startswith("/"):
            permalink = "/" + permalink

        if permalink.endswith("index.html"):
            permalink = permalink[: -1 * len("index.html")]
        return permalink


class PaginationSitePage(SitePage):
    def __init__(
        self,
        source: "PageFile",
        data: Dict,
        collections: Dict[str, List["PageFile"]],
        index: int,
        items: List,
    ) -> None:
        super().__init__(source, data, collections)
        self.index = index
        self.items = items
        self.template_data = {
            **self.template_data,
            "items": self.items,
            "index": self.index,
        }

    def get_path(self) -> Path:
        if self.index == 0:
            return super().get_path()
        else:
            if "permalink" in self.data:
                jinja2_env = jinja2.Environment()
                permalink_template = jinja2_env.from_string(self.data["permalink"])
                permalink = permalink_template.render(
                    data=self.data, index=self.index, items=self.items
                )
                if permalink.endswith("/"):
                    # Filename is not specified, so append 'index.html'
                    return Path(permalink) / "index.html"
                else:
                    # Assume the last part of the path is the filename
                    return Path(permalink)
            else:
                path = self.source.path
                return path.parent / path.stem / str(self.index) / "index.html"


class InvalidFileExtensionException(Exception):
    pass


class InvalidTagsException(Exception):
    pass


class MissingPaginationSourceException(Exception):
    pass


class SourceFile(ABC):
    suffixes: set

    def __init__(self, path: Path) -> None:
        if path.suffix not in self.suffixes:
            raise InvalidFileExtensionException(path.suffix)
        self.path = path
        self.date = arrow.get(os.path.getmtime(self.path))

    def __str__(self):
        return str(self.path)


class NoPermalinkException(Exception):
    pass


class PageFile(SourceFile):
    def __init__(self, path: Path, data: Dict) -> None:
        super().__init__(path)

        with open(self.path) as infile:
            metadata, self.content = frontmatter.parse(infile.read())

        self.data = {**data, **metadata}

        if "tags" in self.data:
            if isinstance(self.data["tags"], str):
                self.tags = set()
                self.tags.add(self.data["tags"])
            elif isinstance(self.data["tags"], List):
                self.tags = set(self.data["tags"])
            else:
                raise InvalidTagsException(
                    f"Invalid tags for file at {self.path}. Expected <str> or <list>, "
                    f"got {type(self.data['tags'])}"
                )
        else:
            self.tags = set()

        if "date" in self.data:
            self.date = arrow.get(self.data["date"])

    def get_pages(self, collections: Dict[str, List["PageFile"]]) -> List[SitePage]:
        if "pagination" in self.data:

            pagination_source = self.data["pagination"]["data"]

            if pagination_source in self.data:
                pagination_data = self.data[pagination_source]
            elif pagination_source in collections:
                pagination_data = collections[pagination_source]
            else:
                raise MissingPaginationSourceException(pagination_source)

            pages: List[SitePage] = []
            for index, items in enumerate(
                chunks(pagination_data, self.data["pagination"]["size"])
            ):
                pages.append(
                    PaginationSitePage(self, self.data, collections, index, items)
                )
            return pages
        else:
            return [SitePage(self, self.data, collections)]

    def get_permalink(self):
        if "pagination" in self.data:
            raise NoPermalinkException(
                "Cannot get a permalink from a PageFile with pagination"
            )

        return SitePage(self, self.data, []).get_permalink()

    def get_html(self, jinja2_env, **kwargs):
        return self.content


class MarkdownFile(PageFile):
    suffixes = {".md"}

    def get_html(self, _, **kwargs):
        return markdown.markdown(self.content, extensions=["codehilite", "fenced_code"])


class Jinja2File(PageFile):
    def get_html(self, jinja2_env, **kwargs):
        template = jinja2_env.from_string(self.content)
        return template.render(**kwargs)

    suffixes = {".html", ".j2"}


class DataFile(SourceFile, ABC):
    @abstractmethod
    def get_data(self):  # pragma: no cover
        return


class JSONFile(DataFile):
    suffixes = {".json"}

    def get_data(self) -> Union[List, Dict]:
        with open(self.path) as infile:
            return json.load(infile)


class PythonFile(DataFile):
    suffixes = {".py"}

    def get_data(self) -> Any:
        parent_path = str(self.path.parent)
        if self.path.parent.name != "":
            sys.path.append(parent_path)
            module = __import__(self.path.stem)
            importlib.reload(module)
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

    def load_source_file(self, path: Path, data: Dict) -> PageFile:
        suffix = path.suffix
        if not self.is_valid_file(path):
            raise InvalidFileExtensionException(
                f"No PageFile type found with suffix {suffix}"
            )

        return self.suffix_to_class_map[suffix](path, data)
