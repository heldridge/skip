from pathlib import Path


class SitePage:
    pass


class InvalidFileExtensionException(Exception):
    pass


class SourceFile:
    suffix: str

    def __init__(self, path) -> None:
        if path.suffix != self.suffix:
            raise InvalidFileExtensionException(path.suffix)

        self.path = path


class PageFile(SourceFile):
    def get_pages(self) -> list[SitePage]:
        pass


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
