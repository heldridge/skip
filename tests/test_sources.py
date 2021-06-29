from pathlib import Path
import unittest

from sources import (
    HTMLFile,
    InvalidFileExtensionException,
    Jinja2File,
    MarkdownFile,
    SourceFileFactory,
)


class TestSourceFileFactory(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sff = SourceFileFactory()
        return super().setUpClass()

    def test_accepts_known_extensions(self):
        for file in ["pagination.j2", "single-tag.md", "tags.html", "my-data.py"]:
            path = Path(f"tests/files/{file}")
            self.sff.load_source_file(path, {})

    def test_rejects_unknown_extensions(self):
        for extension in {".htmx", ".doc", ".njk"}:
            path = Path(f"file{extension}")
            with self.assertRaises(InvalidFileExtensionException) as context:
                self.sff.load_source_file(path, {})

            self.assertTrue(extension in str(context.exception))


class TestPageFile(unittest.TestCase):
    def test_loads_tags(self):
        path = Path("tests/files/tags.html")

        page_file = HTMLFile(path, {})
        self.assertEqual(page_file.tags, {"a", "b", "c"})

    def test_loads_single_tag(self):
        path = Path("tests/files/single-tag.md")

        page_file = MarkdownFile(path, {})
        self.assertEqual(page_file.tags, {"a"})


class TestGetPages(unittest.TestCase):
    def test_returns_single_page(self):
        html_file = HTMLFile(Path("tests/files/tags.html"), {})
        pages = html_file.get_pages({})
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0].source.content, "<h1>Hello</h1>")

    def test_size_1_pagination(self):
        j2_file = Jinja2File(Path("tests/files/pagination.j2"), {})
        pages = j2_file.get_pages({"a": ["dummy1", "dummy2"]})
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0].items, ["dummy1"])

    def test_size_2_pagination(self):
        j2_file = Jinja2File(Path("tests/files/pagination2.j2"), {})
        pages = j2_file.get_pages({})
        self.assertEqual(len(pages), 3)
        self.assertEqual(pages[1].items, ["c", "d"])
