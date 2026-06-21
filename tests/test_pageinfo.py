"""
Tests for _doctools/pageinfo.py:
  - extract_frontmatter_and_content
  - count_words
  - find_markdown_files
  - save_to_csv
"""
import csv
import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_doctools"),
)

from pageinfo import (
    count_words,
    extract_frontmatter_and_content,
    find_markdown_files,
    save_to_csv,
)


# ---------------------------------------------------------------------------
# extract_frontmatter_and_content
# ---------------------------------------------------------------------------

class TestExtractFrontmatterAndContent:
    def test_with_valid_frontmatter(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("---\ntitle: Hello\ncontentType: overview\n---\nSome content here.")

        frontmatter, content = extract_frontmatter_and_content(str(md_file))

        assert frontmatter == {"title": "Hello", "contentType": "overview"}
        assert content == "Some content here."

    def test_without_frontmatter(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Just content\nNo frontmatter here.")

        frontmatter, content = extract_frontmatter_and_content(str(md_file))

        assert frontmatter is None
        assert "Just content" in content

    def test_with_invalid_yaml_frontmatter(self, tmp_path):
        md_file = tmp_path / "test.md"
        # Mapping key collision causes yaml.YAMLError with the safe_load call
        md_file.write_text("---\nkey: [unclosed\n---\nContent here.")

        frontmatter, content = extract_frontmatter_and_content(str(md_file))

        assert frontmatter is None
        assert content == "Content here."

    def test_content_is_stripped(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("---\ntitle: Test\n---\n\n  Content with spaces.  \n\n")

        _, content = extract_frontmatter_and_content(str(md_file))

        assert content == "Content with spaces."

    def test_null_frontmatter_value(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("---\ntitle: \ncontentType: tutorial\n---\nContent.")

        frontmatter, _ = extract_frontmatter_and_content(str(md_file))

        assert frontmatter["contentType"] == "tutorial"
        assert frontmatter["title"] is None

    def test_list_content_type(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("---\ncontentType:\n  - overview\n  - tutorial\n---\nContent.")

        frontmatter, _ = extract_frontmatter_and_content(str(md_file))

        assert frontmatter["contentType"] == ["overview", "tutorial"]

    def test_empty_file_returns_none_frontmatter(self, tmp_path):
        md_file = tmp_path / "empty.md"
        md_file.write_text("")

        frontmatter, content = extract_frontmatter_and_content(str(md_file))

        assert frontmatter is None
        assert content == ""

    def test_frontmatter_only_no_body(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("---\ntitle: No body\n---\n")

        frontmatter, content = extract_frontmatter_and_content(str(md_file))

        assert frontmatter == {"title": "No body"}
        assert content == ""

    def test_numeric_frontmatter_value(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("---\nweight: 10\n---\nContent.")

        frontmatter, _ = extract_frontmatter_and_content(str(md_file))

        assert frontmatter["weight"] == 10

    def test_multiple_frontmatter_keys(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text(
            "---\ntitle: Multi\ndescription: desc\ntags: [a, b]\n---\nBody."
        )

        frontmatter, content = extract_frontmatter_and_content(str(md_file))

        assert frontmatter["title"] == "Multi"
        assert frontmatter["description"] == "desc"
        assert frontmatter["tags"] == ["a", "b"]
        assert content == "Body."


# ---------------------------------------------------------------------------
# count_words
# ---------------------------------------------------------------------------

class TestCountWords:
    def test_simple_sentence(self):
        assert count_words("hello world") == 2

    def test_empty_string(self):
        assert count_words("") == 0

    def test_single_word(self):
        assert count_words("hello") == 1

    def test_multiple_spaces_treated_as_one_delimiter(self):
        assert count_words("one  two   three") == 3

    def test_leading_trailing_whitespace_ignored(self):
        assert count_words("  hello world  ") == 2

    def test_newlines_count_as_delimiters(self):
        assert count_words("line one\nline two") == 4

    def test_tabs_count_as_delimiters(self):
        assert count_words("word1\tword2") == 2

    def test_markdown_formatting_counted_as_words(self):
        # The function splits on whitespace only; markdown symbols are kept as tokens.
        # "# Heading\n\nSome **bold** text." → ['#', 'Heading', 'Some', '**bold**', 'text.'] = 5
        text = "# Heading\n\nSome **bold** text."
        assert count_words(text) == 5

    def test_numbers_counted_as_words(self):
        assert count_words("item 1 item 2") == 4

    def test_long_text(self):
        words = ["word"] * 100
        assert count_words(" ".join(words)) == 100


# ---------------------------------------------------------------------------
# find_markdown_files
# ---------------------------------------------------------------------------

class TestFindMarkdownFiles:
    def test_finds_md_files_in_root(self, tmp_path):
        (tmp_path / "doc1.md").write_text("# Doc 1")
        (tmp_path / "doc2.md").write_text("# Doc 2")

        files = find_markdown_files(str(tmp_path))

        assert len(files) == 2

    def test_finds_md_files_recursively(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "root.md").write_text("root")
        (sub / "nested.md").write_text("nested")

        files = find_markdown_files(str(tmp_path))

        assert len(files) == 2

    def test_ignores_non_md_files(self, tmp_path):
        (tmp_path / "doc.md").write_text("markdown")
        (tmp_path / "image.png").write_bytes(b"")
        (tmp_path / "config.yml").write_text("key: value")
        (tmp_path / "script.py").write_text("# python")

        files = find_markdown_files(str(tmp_path))

        assert len(files) == 1

    def test_returns_strings(self, tmp_path):
        (tmp_path / "doc.md").write_text("content")

        files = find_markdown_files(str(tmp_path))

        assert all(isinstance(f, str) for f in files)

    def test_empty_directory_returns_empty_list(self, tmp_path):
        assert find_markdown_files(str(tmp_path)) == []

    def test_deeply_nested_files_are_found(self, tmp_path):
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "deep.md").write_text("deep content")

        files = find_markdown_files(str(tmp_path))

        assert len(files) == 1
        assert "deep.md" in files[0]


# ---------------------------------------------------------------------------
# save_to_csv
# ---------------------------------------------------------------------------

class TestSaveToCSV:
    def test_header_row_contains_correct_columns(self, tmp_path):
        csv_path = str(tmp_path / "out.csv")
        save_to_csv([["file1.md", "overview", 100]], csv_path)

        with open(csv_path, newline="") as f:
            header = next(csv.reader(f))

        assert header == ["Filename", "WordCount", "ContentType_1"]

    def test_data_row_matches_input(self, tmp_path):
        csv_path = str(tmp_path / "out.csv")
        save_to_csv([["file1.md", "overview", 100]], csv_path)

        with open(csv_path, newline="") as f:
            rows = list(csv.reader(f))

        assert rows[1] == ["file1.md", "100", "overview"]

    def test_list_content_type_expands_to_multiple_columns(self, tmp_path):
        csv_path = str(tmp_path / "out.csv")
        save_to_csv([["file1.md", ["overview", "tutorial"], 200]], csv_path)

        with open(csv_path, newline="") as f:
            rows = list(csv.reader(f))

        assert "ContentType_1" in rows[0]
        assert "ContentType_2" in rows[0]
        assert rows[1][2] == "overview"
        assert rows[1][3] == "tutorial"

    def test_shorter_content_type_lists_are_padded(self, tmp_path):
        csv_path = str(tmp_path / "out.csv")
        data = [
            ["file1.md", ["a", "b", "c"], 100],
            ["file2.md", ["x"], 50],
        ]
        save_to_csv(data, csv_path)

        with open(csv_path, newline="") as f:
            rows = list(csv.reader(f))

        # Both data rows should have the same number of columns as the header
        assert len(rows[1]) == len(rows[0])
        assert len(rows[2]) == len(rows[0])
        # file2 trailing columns should be empty
        assert rows[2][3] == ""
        assert rows[2][4] == ""

    def test_multiple_rows_written(self, tmp_path):
        csv_path = str(tmp_path / "out.csv")
        data = [
            ["a.md", "intro", 50],
            ["b.md", "reference", 200],
            ["c.md", "tutorial", 150],
        ]
        save_to_csv(data, csv_path)

        with open(csv_path, newline="") as f:
            rows = list(csv.reader(f))

        # 1 header + 3 data rows
        assert len(rows) == 4

    def test_empty_content_type_string(self, tmp_path):
        csv_path = str(tmp_path / "out.csv")
        save_to_csv([["file.md", "", 10]], csv_path)

        with open(csv_path, newline="") as f:
            rows = list(csv.reader(f))

        assert rows[1][2] == ""

    def test_word_count_written_as_string(self, tmp_path):
        """CSV always stores values as strings."""
        csv_path = str(tmp_path / "out.csv")
        save_to_csv([["file.md", "overview", 42]], csv_path)

        with open(csv_path, newline="") as f:
            rows = list(csv.reader(f))

        assert rows[1][1] == "42"
