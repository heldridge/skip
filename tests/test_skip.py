import json
from pathlib import Path
import tempfile
import unittest

import arrow

from skip_ssg import skip
from skip_ssg.sources import MarkdownFile


class TestWritePage(unittest.TestCase):
    def test_writes_page(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            skip.write_page(td, Path("a/b/c"), Path("x/y/z"), "dummy", True)
            full_path = td / Path("a/b/c")

            self.assertTrue(full_path.exists())


class TestGetPageFiles(unittest.TestCase):
    def test_loads_right_data(self):
        page_files = skip.get_page_files(
            {},
            lambda _: False,
            Path("tests/files/demo_site/"),
            {"global": "global"},
            True,
        )

        for pf in page_files:
            # All get parent directory data
            self.assertTrue("top" in pf.data)

            # All get global data
            self.assertTrue("global" in pf.data)

            if "sub-a" in pf.path.parts:
                self.assertTrue("a_json" in pf.data)
                self.assertTrue("a_py" in pf.data)
                self.assertFalse("b_json" in pf.data)
                self.assertFalse("b_py" in pf.data)

            elif "sub-b" in pf.path.parts:
                self.assertFalse("a_json" in pf.data)
                self.assertFalse("a_py" in pf.data)
                self.assertTrue("b_json" in pf.data)
                self.assertTrue("b_py" in pf.data)


class TestGetCollections(unittest.TestCase):
    def test_creates_all_collection(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with open(td / "a.md", "w+") as outfile:
                outfile.write("# A")
            with open(td / "b.md", "w+") as outfile:
                outfile.write("# B")

            pfA = MarkdownFile(td / "a.md", {})
            pfB = MarkdownFile(td / "b.md", {})

            collections = skip.get_collections([pfA, pfB])

            self.assertTrue("all" in collections)
            self.assertTrue(len(collections["all"]) == 2)

    def test_sorts_by_date(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            with open(td / "a.md", "w+") as outfile:
                outfile.write("# A")

            with open(td / "b.md", "w+") as outfile:
                outfile.write("# B")

            pfA = MarkdownFile(td / "a.md", {})
            pfB = MarkdownFile(td / "b.md", {})

            pfA.date = arrow.get("2021-01-01")
            pfB.date = arrow.get("2021-01-02")

            collections = skip.get_collections([pfB, pfA])

            self.assertTrue(collections["all"][0].path == td / "a.md")
