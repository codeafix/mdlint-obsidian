"""Callout rules.

Rules
-----
callout-invalid-type        (WARNING): > [!type] where type is not one of the
                             13 built-in types or their aliases.
callout-missing-continuation (ERROR) : The line immediately after a callout
                             header is non-empty and does not start with >.
callout-invalid-modifier     (ERROR) : The modifier after the callout type is
                             not + or -.
"""

from __future__ import annotations

import re

from ..models import LintError, Severity
from ..utils import get_frontmatter_end, is_in_code_block

# All built-in callout type tokens (case-insensitive)
_VALID_TYPES: frozenset[str] = frozenset(
    {
        "note",
        "abstract", "summary", "tldr",
        "info",
        "todo",
        "tip", "hint", "important",
        "success", "check", "done",
        "question", "help", "faq",
        "warning", "caution", "attention",
        "failure", "fail", "missing",
        "danger", "error",
        "bug",
        "example",
        "quote", "cite",
    }
)

# Matches:  > [!type...]  capturing the type and everything up to the closing ]
# Groups: (type, rest_before_bracket)
# rest_before_bracket may be empty, '+', '-', or something invalid like '*'
_CALLOUT_RE = re.compile(
    r"^\s*>\s*\[!([A-Za-z0-9_-]+)([^\]]*)\]",
    re.IGNORECASE,
)


def check(lines: list[str], vault_path: str | None = None) -> list[LintError]:
    errors: list[LintError] = []
    fm_end = get_frontmatter_end(lines)
    total = len(lines)

    for i, line in enumerate(lines):
        if i < fm_end:
            continue
        if is_in_code_block(lines, i):
            continue

        m = _CALLOUT_RE.match(line)
        if m is None:
            continue

        callout_type = m.group(1)
        modifier_text = m.group(2)  # everything between type and ']', e.g. '' / '+' / '-' / '*' / ' title'

        # A valid modifier is empty (no modifier), '+', or '-'.
        # Anything else (e.g. '*', '!') is invalid.
        if modifier_text and modifier_text not in ("+", "-"):
            errors.append(
                LintError(
                    rule="callout-invalid-modifier",
                    severity=Severity.ERROR,
                    line=i + 1,
                    message=f"Callout modifier '{modifier_text}' is not '+' or '-'",
                )
            )

        # callout-invalid-type (WARNING — custom CSS types are valid)
        if callout_type.lower() not in _VALID_TYPES:
            errors.append(
                LintError(
                    rule="callout-invalid-type",
                    severity=Severity.WARNING,
                    line=i + 1,
                    message=f"Unknown callout type '[!{callout_type}]'; "
                    "not one of the built-in types",
                )
            )

        # callout-missing-continuation: the IMMEDIATELY next line must start with >
        # A blank line ends the callout block (like any Markdown blockquote),
        # so we only inspect line i+1, not the next non-blank line.
        next_idx = i + 1
        if next_idx < total:
            next_line = lines[next_idx]
            if next_line.strip() and not next_line.lstrip().startswith(">"):
                errors.append(
                    LintError(
                        rule="callout-missing-continuation",
                        severity=Severity.ERROR,
                        line=next_idx + 1,
                        message="Callout body line does not start with '>'",
                    )
                )

    return errors
