"""Math rules.

Rules
-----
unclosed-math-block  : $$ opened but not closed (document-level).
unclosed-inline-math : $ opened but not closed on the same line.
                       Conservative: only flags when the opening $ is followed
                       by a non-whitespace, non-digit character to avoid
                       false positives on currency symbols like $100.
"""

from __future__ import annotations

from ..models import LintError, Severity
from ..utils import get_frontmatter_end, is_in_code_block


def check(lines: list[str], vault_path: str | None = None) -> list[LintError]:
    errors: list[LintError] = []
    fm_end = get_frontmatter_end(lines)

    errors.extend(_check_math_blocks(lines, fm_end))
    errors.extend(_check_inline_math(lines, fm_end))

    return errors


def _check_math_blocks(lines: list[str], fm_end: int) -> list[LintError]:
    """Detect unclosed $$ math blocks (document-level)."""
    errors: list[LintError] = []
    in_block = False
    open_line = 0

    for i, line in enumerate(lines):
        if i < fm_end:
            continue
        if is_in_code_block(lines, i):
            continue

        stripped = line.strip()
        # A block math delimiter is a line that is *only* $$
        if stripped == "$$":
            if not in_block:
                in_block = True
                open_line = i + 1
            else:
                in_block = False

    if in_block:
        errors.append(
            LintError(
                rule="unclosed-math-block",
                severity=Severity.ERROR,
                line=open_line,
                message="Math block $$ is opened but never closed",
            )
        )

    return errors


def _check_inline_math(lines: list[str], fm_end: int) -> list[LintError]:
    """Detect unclosed inline $...$ on each line (conservative)."""
    errors: list[LintError] = []

    for i, line in enumerate(lines):
        if i < fm_end:
            continue
        if is_in_code_block(lines, i):
            continue
        # Skip lines that are pure math-block delimiters
        if line.strip() == "$$":
            continue

        result = _scan_inline_math(line)
        if result is not None:
            errors.append(
                LintError(
                    rule="unclosed-inline-math",
                    severity=Severity.WARNING,
                    line=i + 1,
                    message="Inline math $ is opened but not closed on this line",
                )
            )

    return errors


def _scan_inline_math(line: str) -> bool | None:
    """Return True if the line has an unclosed inline math expression.

    Returns None (no error) if the unclosed $ looks like a currency symbol
    (i.e., followed immediately by a digit or space).
    """
    in_math = False
    math_opener_pos = -1
    math_opener_next_char = ""
    i = 0
    n = len(line)

    while i < n:
        c = line[i]

        # Skip escaped characters
        if c == "\\":
            i += 2
            continue

        # Skip $$ (block math marker embedded in a line)
        if line[i : i + 2] == "$$":
            i += 2
            continue

        if c == "$":
            next_char = line[i + 1] if i + 1 < n else ""
            if not in_math:
                in_math = True
                math_opener_pos = i
                math_opener_next_char = next_char
            else:
                in_math = False
            i += 1
            continue

        i += 1

    if not in_math:
        return None

    # Conservative: only flag if the opening $ is followed by a non-whitespace,
    # non-digit character (reduces currency false positives).
    if math_opener_next_char == "" or math_opener_next_char.isspace():
        return None
    if math_opener_next_char.isdigit():
        return None

    return True
