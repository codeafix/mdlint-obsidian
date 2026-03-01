"""Tests for frontmatter rules."""

import pytest
from mdlint_obsidian import validate


class TestFrontmatterValid:
    def test_no_frontmatter(self):
        content = "# Hello\n\nThis is a note."
        assert validate(content) == []

    def test_valid_frontmatter(self):
        content = "---\ntitle: My Note\ntags: [foo, bar]\n---\n\n# Hello"
        assert validate(content) == []

    def test_valid_frontmatter_empty(self):
        content = "---\n---\n\n# Hello"
        assert validate(content) == []


class TestFrontmatterNotFirst:
    def test_misplaced_frontmatter(self):
        content = "# Hello\n\n---\ntitle: My Note\n---\n"
        errors = validate(content)
        assert any(e.rule == "frontmatter-not-first" for e in errors)

    def test_misplaced_frontmatter_line_number(self):
        content = "# Hello\n\n---\ntitle: My Note\n---\n"
        errors = validate(content)
        fm_errors = [e for e in errors if e.rule == "frontmatter-not-first"]
        assert len(fm_errors) == 1
        assert fm_errors[0].line == 3

    def test_horizontal_rule_not_flagged(self):
        # A lone --- with no closing --- and no YAML content is a horizontal rule
        content = "# Hello\n\n---\n\n# World"
        errors = validate(content)
        assert not any(e.rule == "frontmatter-not-first" for e in errors)


class TestFrontmatterUnclosed:
    def test_unclosed_frontmatter(self):
        content = "---\ntitle: My Note\n\n# Hello"
        errors = validate(content)
        assert any(e.rule == "frontmatter-unclosed" for e in errors)

    def test_unclosed_frontmatter_at_line_1(self):
        content = "---\ntitle: My Note\n"
        errors = validate(content)
        fm_errors = [e for e in errors if e.rule == "frontmatter-unclosed"]
        assert len(fm_errors) == 1
        assert fm_errors[0].line == 1


class TestFrontmatterInvalidYaml:
    def test_invalid_yaml(self):
        content = "---\ntitle: [\ninvalid yaml here\n---\n"
        errors = validate(content)
        assert any(e.rule == "frontmatter-invalid-yaml" for e in errors)

    def test_invalid_yaml_duplicate_key(self):
        content = "---\ntitle: First\ntitle: Second\n---\n"
        # PyYAML allows duplicate keys (last wins), so this should NOT error
        errors = validate(content)
        assert not any(e.rule == "frontmatter-invalid-yaml" for e in errors)

    def test_valid_yaml_not_flagged(self):
        content = "---\ntitle: 'hello: world'\ntags:\n  - foo\n  - bar\n---\n"
        errors = validate(content)
        assert not any(e.rule == "frontmatter-invalid-yaml" for e in errors)
