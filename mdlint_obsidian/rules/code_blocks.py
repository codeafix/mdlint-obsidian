"""Code block rules.

Rules
-----
unclosed-code-block : An opening fence (``` or ~~~) has no matching closing fence.
"""

from __future__ import annotations

from ..models import LintError, Severity
from ..utils import get_code_block_ranges, get_frontmatter_end


def check(lines: list[str], vault_path: str | None = None) -> list[LintError]:
    errors: list[LintError] = []
    fm_end = get_frontmatter_end(lines)

    # get_code_block_ranges already handles detection.  An unclosed block is
    # one whose range extends to the last line of the document without a proper
    # closing fence.  We detect this by re-running the fence-scanner and
    # checking whether the block was closed.
    in_block = False
    fence_char = ""
    fence_len = 0
    start_line = 0

    for i, line in enumerate(lines):
        if i < fm_end:
            continue

        stripped = line.strip()

        if not in_block:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence_char = stripped[0]
                j = 0
                while j < len(stripped) and stripped[j] == fence_char:
                    j += 1
                fence_len = j
                in_block = True
                start_line = i
        else:
            candidate = stripped.rstrip()
            if (
                candidate
                and all(c == fence_char for c in candidate)
                and len(candidate) >= fence_len
            ):
                in_block = False
                fence_char = ""
                fence_len = 0

    if in_block:
        errors.append(
            LintError(
                rule="unclosed-code-block",
                severity=Severity.ERROR,
                line=start_line + 1,
                message=f"Code block opened with {'`' * fence_len} is never closed",
            )
        )

    return errors
