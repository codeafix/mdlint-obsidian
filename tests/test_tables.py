"""Tests for table rules."""

import pytest
from mdlint_obsidian import validate


class TestTableValid:
    def test_simple_valid_table(self):
        content = "| A | B | C |\n|---|---|---|\n| 1 | 2 | 3 |"
        assert validate(content) == []

    def test_table_with_alignment(self):
        content = "| A | B |\n|:--|--:|\n| x | y |"
        assert validate(content) == []

    def test_no_tables(self):
        assert validate("Just plain text.") == []

    def test_multiple_valid_tables(self):
        content = (
            "| A | B |\n|---|---|\n| 1 | 2 |\n\n"
            "| X | Y | Z |\n|---|---|---|\n| a | b | c |"
        )
        assert validate(content) == []


class TestTableMissingSeparator:
    def test_missing_separator(self):
        content = "| A | B |\n| 1 | 2 |"
        errors = validate(content)
        assert any(e.rule == "table-missing-separator" for e in errors)

    def test_missing_separator_line_number(self):
        content = "Some text\n| A | B |\n| 1 | 2 |"
        errors = validate(content)
        ts = [e for e in errors if e.rule == "table-missing-separator"]
        assert ts[0].line == 2

    def test_not_flagged_inside_code_block(self):
        content = "```\n| A | B |\n| 1 | 2 |\n```"
        errors = validate(content)
        assert not any(e.rule == "table-missing-separator" for e in errors)

    def test_separator_present_no_error(self):
        content = "| A | B |\n|---|---|\n| 1 | 2 |"
        errors = validate(content)
        assert not any(e.rule == "table-missing-separator" for e in errors)


class TestTableInconsistentColumns:
    def test_inconsistent_columns(self):
        content = "| A | B | C |\n|---|---|---|\n| 1 | 2 |"
        errors = validate(content)
        assert any(e.rule == "table-inconsistent-columns" for e in errors)

    def test_inconsistent_columns_line_number(self):
        content = "| A | B |\n|---|---|\n| 1 | 2 | 3 |"
        errors = validate(content)
        tc = [e for e in errors if e.rule == "table-inconsistent-columns"]
        assert tc[0].line == 3

    def test_consistent_columns_no_error(self):
        content = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
        errors = validate(content)
        assert not any(e.rule == "table-inconsistent-columns" for e in errors)

    def test_not_flagged_inside_code_block(self):
        content = "```\n| A | B |\n|---|---|\n| 1 | 2 | 3 |\n```"
        errors = validate(content)
        assert not any(e.rule == "table-inconsistent-columns" for e in errors)
