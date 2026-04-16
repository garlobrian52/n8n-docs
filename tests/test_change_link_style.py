"""
Tests for _doctools/change_link_style.py:
  - find_markdown_files
  - get_url_path_from_file_path
  - map_urls_to_files
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_doctools"),
)

from change_link_style import (
    find_markdown_files,
    get_url_path_from_file_path,
    map_urls_to_files,
)


# ---------------------------------------------------------------------------
# find_markdown_files
# ---------------------------------------------------------------------------

class TestFindMarkdownFiles:
    def test_finds_md_files_in_root(self, tmp_path):
        (tmp_path / "doc.md").write_text("# Doc")
        files = find_markdown_files(str(tmp_path))
        assert len(files) == 1

    def test_finds_md_files_recursively(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "root.md").write_text("root")
        (sub / "nested.md").write_text("nested")

        files = find_markdown_files(str(tmp_path))

        assert len(files) == 2

    def test_matches_uppercase_md_extension(self, tmp_path):
        (tmp_path / "DOC.MD").write_text("# Doc")
        files = find_markdown_files(str(tmp_path))
        assert len(files) == 1

    def test_matches_mixed_case_md_extension(self, tmp_path):
        (tmp_path / "mixed.Md").write_text("# Doc")
        files = find_markdown_files(str(tmp_path))
        assert len(files) == 1

    def test_ignores_non_md_files(self, tmp_path):
        (tmp_path / "doc.txt").write_text("text")
        (tmp_path / "script.py").write_text("# python")
        (tmp_path / "config.yml").write_text("key: value")

        files = find_markdown_files(str(tmp_path))

        assert len(files) == 0

    def test_returns_path_objects(self, tmp_path):
        (tmp_path / "doc.md").write_text("content")
        files = find_markdown_files(str(tmp_path))
        assert all(isinstance(f, Path) for f in files)

    def test_empty_directory_returns_empty_list(self, tmp_path):
        assert find_markdown_files(str(tmp_path)) == []

    def test_deeply_nested_files_are_found(self, tmp_path):
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "deep.md").write_text("deep")

        files = find_markdown_files(str(tmp_path))

        assert len(files) == 1
        assert files[0].name == "deep.md"


# ---------------------------------------------------------------------------
# get_url_path_from_file_path
# ---------------------------------------------------------------------------

class TestGetUrlPathFromFilePath:
    def test_index_md_returns_parent_directory(self):
        path = Path("/docs/guide/index.md")
        result = get_url_path_from_file_path(path)
        assert result == "/docs/guide"

    def test_regular_md_returns_parent_plus_stem(self):
        path = Path("/docs/guide/page.md")
        result = get_url_path_from_file_path(path)
        assert result == "/docs/guide/page"

    def test_root_index_md_returns_root(self):
        path = Path("/index.md")
        result = get_url_path_from_file_path(path)
        assert result == "/"

    def test_nested_regular_page(self):
        path = Path("/docs/api/reference/endpoint.md")
        result = get_url_path_from_file_path(path)
        assert result == "/docs/api/reference/endpoint"

    def test_top_level_regular_page(self):
        path = Path("/about.md")
        result = get_url_path_from_file_path(path)
        assert result == "/about"

    def test_index_md_does_not_include_index_in_url(self):
        path = Path("/section/index.md")
        result = get_url_path_from_file_path(path)
        assert "index" not in result

    def test_result_is_string(self):
        path = Path("/docs/page.md")
        result = get_url_path_from_file_path(path)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# map_urls_to_files
# ---------------------------------------------------------------------------

class TestMapUrlsToFiles:
    def test_regular_md_file_mapped_correctly(self, tmp_path):
        md_file = tmp_path / "page.md"
        md_file.write_text("content")

        result = map_urls_to_files([md_file], str(tmp_path))

        assert "/page" in result
        assert result["/page"] == "/page.md"

    def test_index_md_maps_to_directory_url(self, tmp_path):
        sub = tmp_path / "guide"
        sub.mkdir()
        index_file = sub / "index.md"
        index_file.write_text("content")

        result = map_urls_to_files([index_file], str(tmp_path))

        assert "/guide" in result
        assert result["/guide"] == "/guide/index.md"

    def test_multiple_files_all_mapped(self, tmp_path):
        (tmp_path / "page1.md").write_text("content")
        (tmp_path / "page2.md").write_text("content")

        files = [tmp_path / "page1.md", tmp_path / "page2.md"]
        result = map_urls_to_files(files, str(tmp_path))

        assert len(result) == 2
        assert "/page1" in result
        assert "/page2" in result

    def test_empty_file_list_returns_empty_dict(self, tmp_path):
        result = map_urls_to_files([], str(tmp_path))
        assert result == {}

    def test_nested_file_url_contains_subdirectory(self, tmp_path):
        sub = tmp_path / "section"
        sub.mkdir()
        md_file = sub / "topic.md"
        md_file.write_text("content")

        result = map_urls_to_files([md_file], str(tmp_path))

        assert "/section/topic" in result

    def test_file_path_values_start_with_slash(self, tmp_path):
        md_file = tmp_path / "page.md"
        md_file.write_text("content")

        result = map_urls_to_files([md_file], str(tmp_path))

        for file_path in result.values():
            assert file_path.startswith("/"), f"Expected leading slash: {file_path}"

    def test_url_keys_start_with_slash(self, tmp_path):
        md_file = tmp_path / "page.md"
        md_file.write_text("content")

        result = map_urls_to_files([md_file], str(tmp_path))

        for url in result.keys():
            assert url.startswith("/"), f"Expected leading slash: {url}"

    def test_returns_dict(self, tmp_path):
        result = map_urls_to_files([], str(tmp_path))
        assert isinstance(result, dict)
