"""Tests for footnote rules."""

import pytest
from mdlint_obsidian import validate


class TestFootnotesValid:
    def test_matched_ref_and_def(self):
        content = "Here is a note[^1].\n\n[^1]: This is the footnote."
        assert validate(content) == []

    def test_multiple_matched(self):
        content = (
            "Note A[^a] and Note B[^b].\n\n"
            "[^a]: Definition A.\n"
            "[^b]: Definition B.\n"
        )
        assert validate(content) == []

    def test_no_footnotes(self):
        assert validate("Just plain text.") == []


class TestOrphanedFootnoteRef:
    def test_ref_without_def(self):
        content = "Here is a note[^missing]."
        errors = validate(content)
        assert any(e.rule == "orphaned-footnote-ref" for e in errors)

    def test_ref_without_def_line_number(self):
        content = "Line 1\nHere is a note[^missing]."
        errors = validate(content)
        refs = [e for e in errors if e.rule == "orphaned-footnote-ref"]
        assert refs[0].line == 2

    def test_not_flagged_inside_code_block(self):
        content = "```\nHere is a note[^missing].\n```"
        errors = validate(content)
        assert not any(e.rule == "orphaned-footnote-ref" for e in errors)

    def test_def_line_not_flagged_as_ref(self):
        # [^1]: on its own line is a definition, not a reference
        content = "[^1]: This is the footnote."
        errors = validate(content)
        assert not any(e.rule == "orphaned-footnote-ref" for e in errors)


class TestOrphanedFootnoteDef:
    def test_def_without_ref(self):
        content = "Plain text.\n\n[^unused]: This definition has no reference."
        errors = validate(content)
        assert any(e.rule == "orphaned-footnote-def" for e in errors)

    def test_def_without_ref_line_number(self):
        content = "Plain text.\n\n[^unused]: Orphaned definition."
        errors = validate(content)
        defs = [e for e in errors if e.rule == "orphaned-footnote-def"]
        assert defs[0].line == 3

    def test_not_flagged_inside_code_block(self):
        content = "```\n[^unused]: Definition.\n```"
        errors = validate(content)
        assert not any(e.rule == "orphaned-footnote-def" for e in errors)

    def test_both_ref_and_def_present(self):
        content = "See[^note].\n\n[^note]: The note."
        errors = validate(content)
        assert not any(
            e.rule in ("orphaned-footnote-ref", "orphaned-footnote-def")
            for e in errors
        )
