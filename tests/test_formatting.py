"""Tests for formatting rules (highlight, comments)."""

import pytest
from mdlint_obsidian import validate


class TestHighlightValid:
    def test_closed_highlight(self):
        assert validate("This is ==highlighted== text.") == []

    def test_multiple_closed_highlights(self):
        assert validate("==first== and ==second==") == []

    def test_escaped_equals(self):
        assert validate(r"This is \== not a highlight.") == []

    def test_no_highlights(self):
        assert validate("Plain text without any highlights.") == []


class TestUnclosedHighlight:
    def test_unclosed(self):
        errors = validate("This is ==unclosed text")
        assert any(e.rule == "unclosed-highlight" for e in errors)

    def test_unclosed_line_number(self):
        errors = validate("Line 1\nThis is ==unclosed")
        hl = [e for e in errors if e.rule == "unclosed-highlight"]
        assert hl[0].line == 2

    def test_not_flagged_inside_code_block(self):
        content = "```\nThis is ==unclosed\n```"
        errors = validate(content)
        assert not any(e.rule == "unclosed-highlight" for e in errors)

    def test_unclosed_on_different_lines_independent(self):
        # Each line is checked independently for highlight
        content = "==open on line 1\n==open on line 2"
        errors = validate(content)
        hl = [e for e in errors if e.rule == "unclosed-highlight"]
        assert len(hl) == 2


class TestCommentValid:
    def test_closed_inline_comment(self):
        assert validate("Text %%comment%% more text.") == []

    def test_closed_multiline_comment(self):
        content = "Text %%comment\nspans lines%% end."
        assert validate(content) == []

    def test_no_comments(self):
        assert validate("Plain text without comments.") == []


class TestUnclosedComment:
    def test_unclosed_comment(self):
        errors = validate("Text %%unclosed comment")
        assert any(e.rule == "unclosed-comment" for e in errors)

    def test_unclosed_comment_line_number(self):
        errors = validate("Line 1\nText %%unclosed")
        uc = [e for e in errors if e.rule == "unclosed-comment"]
        assert uc[0].line == 2

    def test_not_flagged_inside_code_block(self):
        content = "```\nText %%unclosed\n```"
        errors = validate(content)
        assert not any(e.rule == "unclosed-comment" for e in errors)

    def test_escaped_percent_not_counted(self):
        # \%% should not be counted as a comment delimiter
        content = r"Text \%% not a comment"
        errors = validate(content)
        assert not any(e.rule == "unclosed-comment" for e in errors)
