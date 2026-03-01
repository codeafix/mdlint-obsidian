"""Embed rules.

Rules
-----
unclosed-embed           : ![[  without matching ]].
empty-embed              : ![[]] with no content.
embed-invalid-dimension  : ![[file|WxH]] where the dimension suffix is malformed.
"""

from __future__ import annotations

import re

from ..models import LintError, Severity
from ..utils import get_frontmatter_end, is_in_code_block

# A valid dimension suffix: a number, optionally followed by xN  (e.g. 300 or 300x200)
_VALID_DIM = re.compile(r"^\d+(x\d+)?$", re.IGNORECASE)
# A pattern that looks like an *intended* dimension (contains only digits and x/X)
_DIM_ATTEMPT = re.compile(r"^[\dxX]+$")


def check(lines: list[str], vault_path: str | None = None) -> list[LintError]:
    errors: list[LintError] = []
    fm_end = get_frontmatter_end(lines)

    for i, line in enumerate(lines):
        if i < fm_end:
            continue
        if is_in_code_block(lines, i):
            continue
        errors.extend(_check_line(line, i + 1))

    return errors


def _check_line(line: str, line_num: int) -> list[LintError]:
    errors: list[LintError] = []
    i = 0
    n = len(line)

    while i < n:
        if line[i] == "\\":
            i += 2
            continue

        # Embed opening  ![[
        if line[i : i + 3] == "![[":
            i += 3
            content_start = i

            # Scan for the matching ]]
            while i < n:
                if line[i : i + 2] == "]]":
                    content = line[content_start:i]
                    i += 2
                    _validate_embed(content, line_num, errors)
                    break
                i += 1
            else:
                errors.append(
                    LintError(
                        rule="unclosed-embed",
                        severity=Severity.ERROR,
                        line=line_num,
                        message="Embed ![[  is not closed with ]]",
                    )
                )
            continue

        i += 1

    return errors


def _validate_embed(content: str, line_num: int, errors: list[LintError]) -> None:
    if not content.strip():
        errors.append(
            LintError(
                rule="empty-embed",
                severity=Severity.ERROR,
                line=line_num,
                message="Embed ![[]] is empty",
            )
        )
        return

    # Check for dimension suffix:  file|suffix
    if "|" in content:
        suffix = content.split("|", 1)[1].strip()
        # Only validate as a dimension if it looks like one was intended
        # (contains only digits and x/X — not an alias with spaces/letters)
        if _DIM_ATTEMPT.match(suffix) and not _VALID_DIM.match(suffix):
            errors.append(
                LintError(
                    rule="embed-invalid-dimension",
                    severity=Severity.ERROR,
                    line=line_num,
                    message=f"Embed dimension suffix is malformed: '{suffix}' "
                    "(expected format: WIDTHxHEIGHT or WIDTH)",
                )
            )
