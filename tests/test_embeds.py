"""Tests for embed rules."""

import pytest
from mdlint_obsidian import validate


class TestEmbedValid:
    def test_simple_image_embed(self):
        assert validate("![[image.png]]") == []

    def test_embed_with_alias(self):
        assert validate("![[image.png|My caption]]") == []

    def test_embed_with_width(self):
        assert validate("![[image.png|300]]") == []

    def test_embed_with_dimensions(self):
        assert validate("![[image.png|300x200]]") == []

    def test_note_embed(self):
        assert validate("![[My Note]]") == []


class TestUnclosedEmbed:
    def test_unclosed(self):
        errors = validate("![[image.png")
        assert any(e.rule == "unclosed-embed" for e in errors)

    def test_unclosed_line_number(self):
        errors = validate("Line 1\n![[image.png")
        em = [e for e in errors if e.rule == "unclosed-embed"]
        assert em[0].line == 2

    def test_not_flagged_inside_code_block(self):
        content = "```\n![[image.png\n```"
        errors = validate(content)
        assert not any(e.rule == "unclosed-embed" for e in errors)


class TestEmptyEmbed:
    def test_empty(self):
        errors = validate("![[]]")
        assert any(e.rule == "empty-embed" for e in errors)

    def test_whitespace_only(self):
        errors = validate("![[ ]]")
        assert any(e.rule == "empty-embed" for e in errors)

    def test_empty_line_number(self):
        errors = validate("First line\n![[]]")
        em = [e for e in errors if e.rule == "empty-embed"]
        assert em[0].line == 2

    def test_not_flagged_inside_code_block(self):
        content = "```\n![[]]\n```"
        errors = validate(content)
        assert not any(e.rule == "empty-embed" for e in errors)


class TestEmbedInvalidDimension:
    def test_missing_height_after_x(self):
        errors = validate("![[image.png|300x]]")
        assert any(e.rule == "embed-invalid-dimension" for e in errors)

    def test_missing_width_before_x(self):
        errors = validate("![[image.png|x200]]")
        assert any(e.rule == "embed-invalid-dimension" for e in errors)

    def test_valid_width_only(self):
        errors = validate("![[image.png|300]]")
        assert not any(e.rule == "embed-invalid-dimension" for e in errors)

    def test_valid_wxh(self):
        errors = validate("![[image.png|300x200]]")
        assert not any(e.rule == "embed-invalid-dimension" for e in errors)

    def test_text_alias_not_flagged(self):
        # "My Image Caption" has spaces/letters — not treated as dimension attempt
        errors = validate("![[image.png|My Image Caption]]")
        assert not any(e.rule == "embed-invalid-dimension" for e in errors)

    def test_dimension_line_number(self):
        errors = validate("Line 1\n![[image.png|300x]]")
        dim = [e for e in errors if e.rule == "embed-invalid-dimension"]
        assert dim[0].line == 2
