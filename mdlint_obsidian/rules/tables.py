"""Table rules.

Rules
-----
table-missing-separator    : Table header row not followed by a separator row (|---|).
table-inconsistent-columns : Rows in a table have different column counts.
"""

from __future__ import annotations

import re

from ..models import LintError, Severity
from ..utils import get_frontmatter_end, is_in_code_block

# A separator cell: optional spaces, optional leading colon, one or more dashes,
# optional trailing colon, optional spaces.
_SEP_CELL_RE = re.compile(r"^\s*:?-+:?\s*$")


def _is_table_row(line: str) -> bool:
    """Return True if the line looks like a Markdown table row."""
    stripped = line.strip()
    return stripped.startswith("|") and "|" in stripped[1:]


def _count_columns(row: str) -> int:
    """Count the number of columns in a pipe-delimited table row."""
    stripped = row.strip()
    # Remove leading and trailing |
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return len(stripped.split("|"))


def _is_separator_row(row: str) -> bool:
    """Return True if the row is a valid table separator (|---|---|)."""
    stripped = row.strip()
    if not stripped.startswith("|"):
        return False
    inner = stripped.strip("|")
    cells = inner.split("|")
    return bool(cells) and all(_SEP_CELL_RE.match(cell) for cell in cells)


def check(lines: list[str], vault_path: str | None = None) -> list[LintError]:
    errors: list[LintError] = []
    fm_end = get_frontmatter_end(lines)
    total = len(lines)
    i = 0

    while i < total:
        if i < fm_end or is_in_code_block(lines, i):
            i += 1
            continue

        if not _is_table_row(lines[i]):
            i += 1
            continue

        # Found the start of a table block
        table_start = i
        header_cols = _count_columns(lines[i])

        # Next line should be the separator
        sep_idx = i + 1
        if sep_idx >= total or not _is_separator_row(lines[sep_idx]):
            errors.append(
                LintError(
                    rule="table-missing-separator",
                    severity=Severity.ERROR,
                    line=table_start + 1,
                    message="Table header row is not followed by a separator row",
                )
            )
            # Advance past consecutive table rows to avoid re-reporting
            while i < total and _is_table_row(lines[i]):
                i += 1
            continue

        # Collect all table rows (header + separator + body)
        i += 2  # skip header and separator
        while i < total and _is_table_row(lines[i]):
            col_count = _count_columns(lines[i])
            if col_count != header_cols:
                errors.append(
                    LintError(
                        rule="table-inconsistent-columns",
                        severity=Severity.ERROR,
                        line=i + 1,
                        message=(
                            f"Table row has {col_count} column(s) but header "
                            f"has {header_cols}"
                        ),
                    )
                )
            i += 1

    return errors
