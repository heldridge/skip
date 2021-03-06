from pathlib import Path
import unittest
from unittest.mock import Mock

import arrow
import jinja2

from skip_ssg.sources import (
    DataFileFactory,
    InvalidFileExtensionException,
    InvalidTagsException,
    JSONFile,
    Jinja2File,
    MarkdownFile,
    MissingPaginationSourceException,
    NoPermalinkException,
    PageFileFactory,
    PaginationSitePage,
    PythonFile,
    SitePage,
)


class TestSourceFileFactories(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pff = PageFileFactory()
        cls.dff = DataFileFactory()
        return super().setUpClass()

    def test_accepts_known_extensions(self):
        for file in ["pagination.j2", "single-tag.md", "tags.html"]:
            path = Path(f"tests/files/{file}")
            self.pff.load_source_file(path, {})

        for file in ["my-data.py", "my-data.json"]:
            path = Path(f"tests/files/{file}")
            self.dff.load_source_file(path)

    def test_rejects_unknown_extensions(self):
        for extension in {".htmx", ".doc", ".njk"}:
            path = Path(f"file{extension}")
            with self.assertRaises(InvalidFileExtensionException) as context:
                self.pff.load_source_file(path, {})
                self.assertTrue(extension in str(context.exception))

            with self.assertRaises(InvalidFileExtensionException) as context:
                self.dff.load_source_file(path)
                self.assertTrue(extension in str(context.exception))


class TestPageFile(unittest.TestCase):
    def test_loads_tags(self):
        path = Path("tests/files/tags.html")

        page_file = Jinja2File(path, {})
        self.assertEqual(page_file.tags, {"a", "b", "c"})

    def test_loads_single_tag(self):
        path = Path("tests/files/single-tag.md")

        page_file = MarkdownFile(path, {})
        self.assertEqual(page_file.tags, {"a"})

    def test_bad_tags(self):
        path = Path("tests/files/layout.md")
        with self.assertRaises(InvalidTagsException):
            MarkdownFile(path, {"tags": {"a": 1, "b": 1}})

    def test_rejects_bad_suffix(self):
        path = Path("a/b/c/file.doc")
        with self.assertRaises(InvalidFileExtensionException) as context:
            Jinja2File(path, {})
            self.assertTrue(".doc" in str(context.exception))

    def test_str(self):
        path = Path("tests/files/tags.html")
        page_file = Jinja2File(path, {})
        self.assertEqual(str(page_file), str(path))

    def test_overrides_date(self):
        path = Path("tests/files/date.md")
        md = MarkdownFile(path, {})
        self.assertEqual(md.date, arrow.get("2021-01-01"))

    def test_gets_permalink(self):
        path = Path("tests/files/tags.html")
        page_file = Jinja2File(path, {})
        self.assertEqual(page_file.get_permalink(), "/tests/files/tags/")

    def test_gets_specified_permalink(self):
        path = Path("tests/files/tags.html")
        page_file = Jinja2File(path, {"permalink": "a/b/c/blah.html"})
        self.assertEqual(page_file.get_permalink(), "/a/b/c/blah.html")

    def test_permalink_does_not_add_second_slash(self):
        path = Path("tests/files/tags.html")
        page_file = Jinja2File(path, {"permalink": "/a/b/c/blah.html"})
        self.assertEqual(page_file.get_permalink(), "/a/b/c/blah.html")

    def test_pagination_permalink_raises_error(self):
        path = Path("tests/files/pagination.j2")
        page_file = Jinja2File(path, {})
        with self.assertRaises(NoPermalinkException):
            page_file.get_permalink()


class TestGetPages(unittest.TestCase):
    def test_returns_single_page(self):
        html_file = Jinja2File(Path("tests/files/tags.html"), {})
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

    def test_errors_on_missing_page_source(self):
        j2_file = Jinja2File(Path("tests/files/pagination.j2"), {})

        with self.assertRaises(MissingPaginationSourceException):
            j2_file.get_pages({"b": ["dummy1", "dummy2"]})


class TestRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.jinja2_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("tests/files/templates")
        )
        return super().setUpClass()

    def test_renders_html(self):
        j2_file = Jinja2File(Path("tests/files/tags.html"), {})
        pages = j2_file.get_pages({})
        html = pages[0].render(self.jinja2_env)
        self.assertEqual("<h1>Hello</h1>", html)

    def test_renders_with_layout(self):
        md_file = MarkdownFile(Path("tests/files/layout.md"), {})
        pages = md_file.get_pages({})
        html = pages[0].render(self.jinja2_env)
        self.assertTrue("<main>" in html)

    def test_renders_with_pagination_items(self):
        j2_file = Jinja2File(Path("tests/files/pagination2.j2"), {})
        pages = j2_file.get_pages({})
        html = pages[0].render(self.jinja2_env)
        self.assertTrue("<p>a</p>" in html)
        self.assertTrue("<p>b</p>" in html)


class TestGetpath(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        return super().setUpClass()

    def test_regular_path(self):
        mock_pagefile = Mock()
        mock_pagefile.path = Path("a/b/c/pagefile.html")
        site_page = SitePage(mock_pagefile, {}, {})

        self.assertEqual(site_page.get_path(), Path("a/b/c/pagefile/index.html"))

    def test_pagination_path_index_0(self):
        mock_pagefile = Mock()
        mock_pagefile.path = Path("a/b/c/pagefile.html")
        pagination_page = PaginationSitePage(mock_pagefile, {}, {}, 0, [])

        self.assertEqual(
            pagination_page.get_path(),
            Path("a/b/c/pagefile/index.html"),
        )

    def test_pagination_path(self):
        mock_pagefile = Mock()
        mock_pagefile.path = Path("a/b/c/pagefile.html")
        pagination_page = PaginationSitePage(mock_pagefile, {}, {}, 2, [])

        self.assertEqual(
            pagination_page.get_path(),
            Path("a/b/c/pagefile/2/index.html"),
        )

    def test_index_does_not_go_to_subfolder(self):
        mock_pagefile = Mock()
        mock_pagefile.path = Path("index.md")
        site_page = SitePage(mock_pagefile, {}, {})

        self.assertEqual(site_page.get_path(), Path("index.html"))

    def test_path_from_data(self):
        mock_pagefile = Mock()
        mock_pagefile.path = Path("a/b/c/pagefile.html")
        site_page = SitePage(mock_pagefile, {"permalink": "x/y/z/index.html"}, {})

        self.assertEqual(site_page.get_path(), Path("x/y/z/index.html"))

    def test_appends_index_html(self):
        mock_pagefile = Mock()
        mock_pagefile.path = Path("a/b/c/pagefile.html")
        site_page = SitePage(mock_pagefile, {"permalink": "x/y/z/"}, {})

        self.assertEqual(site_page.get_path(), Path("x/y/z/index.html"))

    def test_renders_path_as_template(self):
        mock_pagefile = Mock()
        mock_pagefile.path = Path("a/b/c/pagefile.html")
        site_page = SitePage(
            mock_pagefile, {"permalink": "x/{{data.middle}}/z/", "middle": "dummy"}, {}
        )

        self.assertEqual(site_page.get_path(), Path("x/dummy/z/index.html"))


class TestGetData(unittest.TestCase):
    def test_json_file(self):
        json_file = JSONFile(Path("tests/files/my-data.json"))
        self.assertEqual(json_file.get_data(), {"a": 1})

    def test_python_file(self):
        python_file = PythonFile(Path("tests/files/my-data.py"))
        self.assertEqual(python_file.get_data(), ["a", "b", "c"])
