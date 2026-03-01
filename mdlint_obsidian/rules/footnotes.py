"""Footnote rules.

Rules
-----
orphaned-footnote-ref : [^id] reference in body with no matching [^id]: definition.
orphaned-footnote-def : [^id]: definition with no matching [^id] reference in body.
"""

from __future__ import annotations

import re

from ..models import LintError, Severity
from ..utils import get_frontmatter_end, is_in_code_block

# Matches a footnote definition at the start of a line: [^id]:
_DEF_RE = re.compile(r"^\[\^([^\]]+)\]:")

# Matches a footnote reference anywhere on a line: [^id] NOT followed by :
_REF_RE = re.compile(r"\[\^([^\]]+)\](?!:)")


def check(lines: list[str], vault_path: str | None = None) -> list[LintError]:
    errors: list[LintError] = []
    fm_end = get_frontmatter_end(lines)

    refs: dict[str, int] = {}   # id -> first line number (1-indexed)
    defs: dict[str, int] = {}   # id -> line number

    for i, line in enumerate(lines):
        if i < fm_end:
            continue
        if is_in_code_block(lines, i):
            continue

        line_num = i + 1

        # Check for definition first (starts of line)
        def_m = _DEF_RE.match(line)
        if def_m:
            fn_id = def_m.group(1)
            if fn_id not in defs:
                defs[fn_id] = line_num
            continue  # a definition line is not also a reference

        # Check for references anywhere on the line
        for ref_m in _REF_RE.finditer(line):
            fn_id = ref_m.group(1)
            if fn_id not in refs:
                refs[fn_id] = line_num

    # Orphaned references (ref with no def)
    for fn_id, line_num in sorted(refs.items(), key=lambda x: x[1]):
        if fn_id not in defs:
            errors.append(
                LintError(
                    rule="orphaned-footnote-ref",
                    severity=Severity.ERROR,
                    line=line_num,
                    message=f"Footnote reference [^{fn_id}] has no matching definition",
                )
            )

    # Orphaned definitions (def with no ref)
    for fn_id, line_num in sorted(defs.items(), key=lambda x: x[1]):
        if fn_id not in refs:
            errors.append(
                LintError(
                    rule="orphaned-footnote-def",
                    severity=Severity.ERROR,
                    line=line_num,
                    message=f"Footnote definition [^{fn_id}]: has no matching reference",
                )
            )

    errors.sort(key=lambda e: e.line)
    return errors
