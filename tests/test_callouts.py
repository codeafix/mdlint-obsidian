"""Tests for callout rules."""

import pytest
from mdlint_obsidian import validate, Severity


class TestCalloutValid:
    def test_valid_note_callout(self):
        content = "> [!note]\n> This is content."
        assert validate(content) == []

    def test_valid_with_title(self):
        content = "> [!warning] Be careful\n> Watch out here."
        assert validate(content) == []

    def test_valid_foldable_expand(self):
        content = "> [!tip]+\n> Expanded by default."
        assert validate(content) == []

    def test_valid_foldable_collapse(self):
        content = "> [!info]-\n> Collapsed by default."
        assert validate(content) == []

    def test_all_built_in_types(self):
        types = [
            "note", "abstract", "summary", "tldr", "info", "todo",
            "tip", "hint", "important", "success", "check", "done",
            "question", "help", "faq", "warning", "caution", "attention",
            "failure", "fail", "missing", "danger", "error", "bug",
            "example", "quote", "cite",
        ]
        for t in types:
            content = f"> [!{t}]\n> Content."
            errors = validate(content)
            assert not any(e.rule == "callout-invalid-type" for e in errors), (
                f"Type '{t}' was incorrectly flagged"
            )

    def test_case_insensitive_type(self):
        content = "> [!NOTE]\n> Content."
        errors = validate(content)
        assert not any(e.rule == "callout-invalid-type" for e in errors)

    def test_empty_callout_no_continuation_error(self):
        # Callout with no body — followed by blank line — is valid
        content = "> [!note]\n\nSome paragraph."
        errors = validate(content)
        assert not any(e.rule == "callout-missing-continuation" for e in errors)


class TestCalloutInvalidType:
    def test_unknown_type(self):
        content = "> [!mycustomtype]\n> Content."
        errors = validate(content)
        assert any(e.rule == "callout-invalid-type" for e in errors)

    def test_unknown_type_is_warning(self):
        content = "> [!mycustomtype]\n> Content."
        errors = validate(content)
        ct = [e for e in errors if e.rule == "callout-invalid-type"]
        assert ct[0].severity == Severity.WARNING

    def test_unknown_type_line_number(self):
        content = "# Title\n> [!foobar]\n> Body."
        errors = validate(content)
        ct = [e for e in errors if e.rule == "callout-invalid-type"]
        assert ct[0].line == 2

    def test_not_flagged_inside_code_block(self):
        content = "```\n> [!unknowntype]\n> Content.\n```"
        errors = validate(content)
        assert not any(e.rule == "callout-invalid-type" for e in errors)


class TestCalloutMissingContinuation:
    def test_missing_continuation(self):
        content = "> [!note]\nThis line has no >"
        errors = validate(content)
        assert any(e.rule == "callout-missing-continuation" for e in errors)

    def test_missing_continuation_line_number(self):
        content = "> [!note]\nThis line has no >"
        errors = validate(content)
        mc = [e for e in errors if e.rule == "callout-missing-continuation"]
        assert mc[0].line == 2

    def test_proper_continuation_ok(self):
        content = "> [!note]\n> Content here."
        errors = validate(content)
        assert not any(e.rule == "callout-missing-continuation" for e in errors)


class TestCalloutInvalidModifier:
    def test_invalid_modifier(self):
        content = "> [!note*]\n> Content."
        errors = validate(content)
        assert any(e.rule == "callout-invalid-modifier" for e in errors)

    def test_valid_plus_modifier(self):
        content = "> [!note+]\n> Content."
        errors = validate(content)
        assert not any(e.rule == "callout-invalid-modifier" for e in errors)

    def test_valid_minus_modifier(self):
        content = "> [!note-]\n> Content."
        errors = validate(content)
        assert not any(e.rule == "callout-invalid-modifier" for e in errors)
