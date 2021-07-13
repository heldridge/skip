import json
from pathlib import Path
import tempfile
import unittest

import skip


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
            {}, lambda _: False, Path("tests/files/demo_site/"), {"global": "global"}
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

    def test_errors_on_non_dict_json_data(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)

            with open(td / "bad.json", "w+") as outfile:
                json.dump(["list"], outfile)

            with self.assertRaises(skip.NonDictDataFileException):
                skip.get_page_files({}, lambda _: False, Path(td), {})
