"""Main validate() entry point for obsidian-linter."""

from __future__ import annotations

from .models import LintError, Severity
from .rules import (
    callouts,
    code_blocks,
    compatibility,
    embeds,
    footnotes,
    formatting,
    frontmatter,
    math,
    tables,
    wikilinks,
)

__all__ = ["validate", "LintError", "Severity"]

_RULE_MODULES = [
    frontmatter,
    wikilinks,
    embeds,
    callouts,
    code_blocks,
    formatting,
    footnotes,
    tables,
    math,
    compatibility,
]


def validate(content: str, vault_path: str | None = None) -> list[LintError]:
    """Validate Obsidian markdown content and return a list of lint errors.

    Parameters
    ----------
    content:
        The full text of a single Obsidian note.
    vault_path:
        Optional path to the vault root directory.  When provided, the
        ``broken-link`` rule checks that every ``[[wikilink]]`` resolves to
        an existing ``.md`` file inside the vault.

    Returns
    -------
    list[LintError]
        Errors sorted by line number.  Warnings are included unless the caller
        filters by severity.
    """
    lines = content.splitlines()
    errors: list[LintError] = []

    for module in _RULE_MODULES:
        errors.extend(module.check(lines, vault_path=vault_path))

    errors.sort(key=lambda e: (e.line, e.rule))
    return errors
