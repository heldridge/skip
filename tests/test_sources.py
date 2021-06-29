from pathlib import Path
import unittest

from sources import (
    HTMLFile,
    InvalidFileExtensionException,
    MarkdownFile,
    SourceFileFactory,
)


class TestSourceFileFactory(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sff = SourceFileFactory()
        return super().setUpClass()

    def test_accepts_known_extensions(self):
        for file in ["collection.j2", "single-tag.md", "tags.html"]:
            path = Path(f"tests/files/{file}")
            self.sff.load_source_file(path)

    def test_rejects_unknown_extensions(self):
        for extension in {".htmx", ".doc", ".njk", ".json", ".py"}:
            path = Path(f"file{extension}")
            with self.assertRaises(InvalidFileExtensionException) as context:
                self.sff.load_source_file(path)

            self.assertTrue(extension in str(context.exception))


class TestPageFile(unittest.TestCase):
    def test_loads_tags(self):
        path = Path("tests/files/tags.html")

        page_file = HTMLFile(path)
        self.assertEqual(page_file.tags, {"a", "b", "c"})

    def test_loads_single_tag(self):
        path = Path("tests/files/single-tag.md")

        page_file = MarkdownFile(path)
        self.assertEqual(page_file.tags, {"mytag"})
