"""Shared utilities used across rule modules."""

from __future__ import annotations


def get_code_block_ranges(lines: list[str]) -> list[tuple[int, int]]:
    """Return list of (start, end) line index pairs (inclusive) for fenced code blocks.

    Handles both backtick (```) and tilde (~~~) fences.  The closing fence must
    use the same character as the opening fence and be at least as long.
    """
    ranges: list[tuple[int, int]] = []
    in_block = False
    fence_char: str = ""
    fence_len: int = 0
    start: int = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not in_block:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence_char = stripped[0]
                # Count fence length (number of leading fence chars)
                j = 0
                while j < len(stripped) and stripped[j] == fence_char:
                    j += 1
                fence_len = j
                in_block = True
                start = i
        else:
            # A closing fence: same char, at least fence_len, nothing else
            candidate = stripped.rstrip()
            if (
                candidate
                and all(c == fence_char for c in candidate)
                and len(candidate) >= fence_len
            ):
                ranges.append((start, i))
                in_block = False
                fence_char = ""
                fence_len = 0

    # Unclosed block extends to end of document
    if in_block:
        ranges.append((start, len(lines) - 1))

    return ranges


def is_in_code_block(lines: list[str], line_index: int) -> bool:
    """Return True if the given line index is inside a fenced code block."""
    for start, end in get_code_block_ranges(lines):
        if start <= line_index <= end:
            return True
    return False


def get_frontmatter_end(lines: list[str]) -> int:
    """Return the first line index after the frontmatter block.

    Returns 0 if there is no frontmatter (i.e., the file does not start
    with ``---``).  Returns 0 (not past the unclosed marker) if the
    frontmatter is unclosed, so that other rules still process the file.
    """
    if not lines or lines[0].strip() != "---":
        return 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i + 1
    return 0
