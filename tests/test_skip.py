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
