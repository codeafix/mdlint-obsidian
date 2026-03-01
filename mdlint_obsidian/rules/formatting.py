"""Formatting rules (bold, italic, highlight, comments).

Rules
-----
unclosed-highlight : == opened but not closed on the same line.
unclosed-comment   : %% opened but not closed (document-level).

Note: escaped delimiters (\\== and \\%%) are handled correctly.
"""

from __future__ import annotations

from ..models import LintError, Severity
from ..utils import get_frontmatter_end, is_in_code_block


def check(lines: list[str], vault_path: str | None = None) -> list[LintError]:
    errors: list[LintError] = []
    fm_end = get_frontmatter_end(lines)

    # --- unclosed-highlight (per-line) ---
    for i, line in enumerate(lines):
        if i < fm_end:
            continue
        if is_in_code_block(lines, i):
            continue
        if _has_unclosed_highlight(line):
            errors.append(
                LintError(
                    rule="unclosed-highlight",
                    severity=Severity.ERROR,
                    line=i + 1,
                    message="Highlight == is opened but not closed on this line",
                )
            )

    # --- unclosed-comment (document-level) ---
    errors.extend(_check_comments(lines, fm_end))

    return errors


def _has_unclosed_highlight(line: str) -> bool:
    """Return True if the line contains an unclosed == highlight marker."""
    in_highlight = False
    i = 0
    n = len(line)
    while i < n:
        if line[i] == "\\":
            i += 2  # skip escaped character
            continue
        if line[i : i + 2] == "==":
            in_highlight = not in_highlight
            i += 2
            continue
        i += 1
    return in_highlight


def _check_comments(lines: list[str], fm_end: int) -> list[LintError]:
    """Check for unclosed %% comments across the whole document."""
    errors: list[LintError] = []
    in_comment = False
    open_line = 0

    for i, line in enumerate(lines):
        if i < fm_end:
            continue
        if is_in_code_block(lines, i):
            continue

        j = 0
        n = len(line)
        while j < n:
            if line[j] == "\\":
                j += 2
                continue
            if line[j : j + 2] == "%%":
                if not in_comment:
                    in_comment = True
                    open_line = i + 1
                else:
                    in_comment = False
                j += 2
                continue
            j += 1

    if in_comment:
        errors.append(
            LintError(
                rule="unclosed-comment",
                severity=Severity.ERROR,
                line=open_line,
                message="Comment %% is opened but never closed",
            )
        )

    return errors
