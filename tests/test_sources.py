from pathlib import Path
import unittest

from sources import InvalidFileExtensionException, SourceFileFactory


class TestSourceFileFactory(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sff = SourceFileFactory()
        return super().setUpClass()

    def test_accepts_known_extensions(self):
        for extension in [".html", ".md", ".j2"]:
            path = Path(f"file.{extension}")
            self.sff.load_source_file(path)

    def test_rejects_unknown_extensions(self):
        for extension in {".htmx", ".doc", ".njk", ".json", ".py"}:
            path = Path(f"file.{extension}")
            with self.assertRaises(InvalidFileExtensionException) as context:
                self.sff.load_source_file(path)

            self.assertTrue(extension in str(context.exception))
