"""Tests for wikilink rules."""

import pytest
from mdlint_obsidian import validate


class TestWikilinkValid:
    def test_simple_wikilink(self):
        assert validate("See [[My Note]] for details.") == []

    def test_wikilink_with_alias(self):
        assert validate("See [[My Note|this note]] for details.") == []

    def test_wikilink_with_heading(self):
        assert validate("See [[My Note#Introduction]] here.") == []

    def test_wikilink_with_block_ref(self):
        assert validate("See [[My Note^abc123]] here.") == []

    def test_wikilink_heading_then_block(self):
        assert validate("See [[My Note#Intro^abc123]] here.") == []

    def test_same_file_heading_link(self):
        assert validate("Jump to [[#Introduction]].") == []

    def test_multiple_valid_wikilinks(self):
        assert validate("[[Note A]] and [[Note B]] are both valid.") == []


class TestUnclosedWikilink:
    def test_unclosed(self):
        errors = validate("See [[My Note here.")
        assert any(e.rule == "unclosed-wikilink" for e in errors)

    def test_unclosed_line_number(self):
        errors = validate("Line one\nSee [[My Note here.")
        wl = [e for e in errors if e.rule == "unclosed-wikilink"]
        assert wl[0].line == 2

    def test_unclosed_not_flagged_inside_code_block(self):
        content = "```\n[[unclosed\n```"
        errors = validate(content)
        assert not any(e.rule == "unclosed-wikilink" for e in errors)

    def test_embed_not_flagged_as_unclosed_wikilink(self):
        errors = validate("![[image.png]]")
        assert not any(e.rule == "unclosed-wikilink" for e in errors)


class TestEmptyWikilink:
    def test_empty(self):
        errors = validate("[[]]")
        assert any(e.rule == "empty-wikilink" for e in errors)

    def test_whitespace_only(self):
        errors = validate("[[ ]]")
        assert any(e.rule == "empty-wikilink" for e in errors)

    def test_empty_line_number(self):
        errors = validate("First line\n[[]]")
        wl = [e for e in errors if e.rule == "empty-wikilink"]
        assert wl[0].line == 2

    def test_empty_not_inside_code_block(self):
        content = "```\n[[]]\n```"
        errors = validate(content)
        assert not any(e.rule == "empty-wikilink" for e in errors)


class TestWikilinkInvalidChars:
    def test_multiple_hashes(self):
        errors = validate("[[Note#heading#another]]")
        assert any(e.rule == "wikilink-invalid-chars" for e in errors)

    def test_caret_before_hash(self):
        errors = validate("[[Note^block#heading]]")
        assert any(e.rule == "wikilink-invalid-chars" for e in errors)

    def test_single_hash_ok(self):
        errors = validate("[[Note#heading]]")
        assert not any(e.rule == "wikilink-invalid-chars" for e in errors)

    def test_single_caret_ok(self):
        errors = validate("[[Note^blockid]]")
        assert not any(e.rule == "wikilink-invalid-chars" for e in errors)


class TestBrokenLink:
    def test_broken_link_with_vault(self, tmp_path):
        (tmp_path / "ExistingNote.md").write_text("# Existing")
        content = "[[MissingNote]]"
        errors = validate(content, vault_path=str(tmp_path))
        assert any(e.rule == "broken-link" for e in errors)

    def test_resolved_link_no_error(self, tmp_path):
        (tmp_path / "ExistingNote.md").write_text("# Existing")
        content = "[[ExistingNote]]"
        errors = validate(content, vault_path=str(tmp_path))
        assert not any(e.rule == "broken-link" for e in errors)

    def test_case_insensitive_match(self, tmp_path):
        (tmp_path / "MyNote.md").write_text("# Note")
        content = "[[mynote]]"
        errors = validate(content, vault_path=str(tmp_path))
        assert not any(e.rule == "broken-link" for e in errors)

    def test_alias_stripped(self, tmp_path):
        (tmp_path / "RealNote.md").write_text("# Note")
        content = "[[RealNote|My alias]]"
        errors = validate(content, vault_path=str(tmp_path))
        assert not any(e.rule == "broken-link" for e in errors)

    def test_heading_stripped(self, tmp_path):
        (tmp_path / "RealNote.md").write_text("# Note")
        content = "[[RealNote#Introduction]]"
        errors = validate(content, vault_path=str(tmp_path))
        assert not any(e.rule == "broken-link" for e in errors)

    def test_no_vault_no_check(self):
        errors = validate("[[MissingNote]]")
        assert not any(e.rule == "broken-link" for e in errors)

    def test_broken_link_is_warning(self, tmp_path):
        errors = validate("[[Missing]]", vault_path=str(tmp_path))
        bl = [e for e in errors if e.rule == "broken-link"]
        from mdlint_obsidian import Severity
        assert bl[0].severity == Severity.WARNING
