"""Main validate() entry point for obsidian-linter."""

from __future__ import annotations

from pathlib import Path

from .models import LintError, Severity
from .utils import get_code_block_ranges, get_frontmatter_end
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
    fm_end = get_frontmatter_end(lines)
    code_block_lines: frozenset[int] = frozenset(
        i
        for start, end in get_code_block_ranges(lines)
        for i in range(start, end + 1)
    )
    vault_index: dict[str, Path] | None = None
    if vault_path:
        vault_index = {
            f.stem.lower(): f for f in Path(vault_path).rglob("*.md")
        }

    errors: list[LintError] = []
    for module in _RULE_MODULES:
        errors.extend(module.check(
            lines,
            fm_end=fm_end,
            code_block_lines=code_block_lines,
            vault_index=vault_index,
        ))

    errors.sort(key=lambda e: (e.line, e.rule))
    return errors
