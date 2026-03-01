"""Tests for code block rules."""

import pytest
from mdlint_obsidian import validate


class TestCodeBlockValid:
    def test_closed_backtick_fence(self):
        content = "```\nsome code\n```"
        assert validate(content) == []

    def test_closed_tilde_fence(self):
        content = "~~~\nsome code\n~~~"
        assert validate(content) == []

    def test_closed_with_language(self):
        content = "```python\nprint('hello')\n```"
        assert validate(content) == []

    def test_multiple_closed_blocks(self):
        content = "```\nblock 1\n```\n\nSome text\n\n```\nblock 2\n```"
        assert validate(content) == []

    def test_no_code_blocks(self):
        assert validate("# Just a heading\n\nSome text.") == []


class TestUnclosedCodeBlock:
    def test_unclosed_backtick(self):
        content = "```python\nsome code"
        errors = validate(content)
        assert any(e.rule == "unclosed-code-block" for e in errors)

    def test_unclosed_tilde(self):
        content = "~~~\nsome code"
        errors = validate(content)
        assert any(e.rule == "unclosed-code-block" for e in errors)

    def test_unclosed_line_number(self):
        content = "Line 1\nLine 2\n```\nsome code"
        errors = validate(content)
        cb = [e for e in errors if e.rule == "unclosed-code-block"]
        assert cb[0].line == 3

    def test_mismatched_fence_chars(self):
        # Opening ``` but closing ~~~ — should be flagged as unclosed
        content = "```\nsome code\n~~~"
        errors = validate(content)
        assert any(e.rule == "unclosed-code-block" for e in errors)

    def test_second_block_unclosed(self):
        content = "```\nblock 1\n```\n\n```\nblock 2 unclosed"
        errors = validate(content)
        cb = [e for e in errors if e.rule == "unclosed-code-block"]
        assert len(cb) == 1
        assert cb[0].line == 5
