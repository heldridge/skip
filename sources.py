from pathlib import Path
from typing import Generator

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
    suffix: str

    def __init__(self, path: Path) -> None:
        if path.suffix != self.suffix:
            raise InvalidFileExtensionException(path.suffix)
        self.path = path


class PageFile(SourceFile):
    def __init__(self, path: Path) -> None:
        super().__init__(path)

        with open(self.path) as infile:
            self.metadata, self.content = frontmatter.parse(infile.read())

        if "tags" in self.metadata:
            if isinstance(self.metadata["tags"], str):
                self.tags: set[str] = set()
                self.tags.add(self.metadata["tags"])
            elif isinstance(self.metadata["tags"], list):
                self.tags = set(self.metadata["tags"])
            else:
                raise InvalidTagsException(
                    f"Invalid tags for file at {self.path}. Expected <str> or <list>, "
                    f"got {type(self.metadata['tags'])}"
                )

    def get_pages(
        self, data: dict, collections: dict[str, list["PageFile"]]
    ) -> list[SitePage]:
        data = {**data, **self.metadata}
        if "pagination" in self.metadata:

            pagination_source = self.metadata["pagination"]["data"]

            if pagination_source in data:
                pagination_data = data[pagination_source]
            elif pagination_source in collections:
                pagination_data = collections[pagination_source]
            else:
                raise MissingPaginationSourceException(pagination_source)

            pages = []
            for index, items in enumerate(
                chunks(pagination_data, self.metadata["pagination"]["size"])
            ):
                pages.append(PaginationSitePage(self, data, collections, index, items))
            return pages
        else:
            return [SitePage(self, data, collections)]


class HTMLFile(PageFile):
    suffix = ".html"


class MarkdownFile(PageFile):
    suffix = ".md"


class Jinja2File(PageFile):
    suffix = ".j2"


class SourceFileFactory:
    suffix_to_class_map = {".html": HTMLFile, ".md": MarkdownFile, ".j2": Jinja2File}

    def load_source_file(self, path: Path) -> SourceFile:
        suffix = path.suffix
        if suffix not in self.suffix_to_class_map:
            raise InvalidFileExtensionException(
                f"No SourceFile type found with suffix {suffix}"
            )

        return self.suffix_to_class_map[suffix](path)
