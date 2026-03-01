"""Tests for math rules."""

import pytest
from mdlint_obsidian import validate, Severity


class TestMathValid:
    def test_closed_math_block(self):
        content = "$$\nx = y + z\n$$"
        assert validate(content) == []

    def test_closed_inline_math(self):
        assert validate("The equation $x + y = z$ is simple.") == []

    def test_multiple_closed_inline(self):
        assert validate("Use $a$ and $b$ in the formula.") == []

    def test_no_math(self):
        assert validate("Plain text without math.") == []

    def test_currency_not_flagged(self):
        # $100 and $50 look like currency — should NOT be flagged
        assert validate("It costs $100 and $50.") == []

    def test_currency_single_dollar_not_flagged(self):
        # Single $100 — conservative: $ followed by digit, don't flag
        errors = validate("Price: $100")
        assert not any(e.rule == "unclosed-inline-math" for e in errors)


class TestUnclosedMathBlock:
    def test_unclosed_block(self):
        content = "$$\nx = y + z"
        errors = validate(content)
        assert any(e.rule == "unclosed-math-block" for e in errors)

    def test_unclosed_block_line_number(self):
        content = "Line 1\n$$\nx = y"
        errors = validate(content)
        mb = [e for e in errors if e.rule == "unclosed-math-block"]
        assert mb[0].line == 2

    def test_not_flagged_inside_code_block(self):
        content = "```\n$$\nx = y\n```"
        errors = validate(content)
        assert not any(e.rule == "unclosed-math-block" for e in errors)

    def test_closed_block_no_error(self):
        content = "$$\nx = y\n$$"
        errors = validate(content)
        assert not any(e.rule == "unclosed-math-block" for e in errors)


class TestUnclosedInlineMath:
    def test_unclosed_inline_math(self):
        errors = validate("The equation $x + y is incomplete.")
        assert any(e.rule == "unclosed-inline-math" for e in errors)

    def test_unclosed_inline_math_line_number(self):
        errors = validate("Line 1\nThe equation $x + y is incomplete.")
        im = [e for e in errors if e.rule == "unclosed-inline-math"]
        assert im[0].line == 2

    def test_unclosed_inline_math_is_warning(self):
        errors = validate("The equation $x is incomplete.")
        im = [e for e in errors if e.rule == "unclosed-inline-math"]
        assert im[0].severity == Severity.WARNING

    def test_not_flagged_inside_code_block(self):
        content = "```\nThe equation $x + y is incomplete.\n```"
        errors = validate(content)
        assert not any(e.rule == "unclosed-inline-math" for e in errors)

    def test_closed_inline_math_no_error(self):
        errors = validate("The value is $x + y$.")
        assert not any(e.rule == "unclosed-inline-math" for e in errors)
