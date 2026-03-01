"""Wikilink rules.

Rules
-----
unclosed-wikilink      : [[ without matching ]].
empty-wikilink         : [[]] with no content.
wikilink-invalid-chars : Wikilink target contains # or ^ in invalid positions.
broken-link (WARNING)  : [[Note]] does not resolve to an existing .md file
                         (only when vault_path is provided).
"""

from __future__ import annotations

from pathlib import Path

from ..models import LintError, Severity
from ..utils import get_frontmatter_end, is_in_code_block


def check(lines: list[str], vault_path: str | None = None) -> list[LintError]:
    errors: list[LintError] = []
    fm_end = get_frontmatter_end(lines)

    # Build vault index for broken-link checks (case-insensitive stem lookup)
    vault_index: dict[str, Path] | None = None
    if vault_path:
        vault_index = {
            f.stem.lower(): f for f in Path(vault_path).rglob("*.md")
        }

    for i, line in enumerate(lines):
        if i < fm_end:
            continue
        if is_in_code_block(lines, i):
            continue
        errors.extend(_check_line(line, i + 1, vault_index))

    return errors


def _check_line(
    line: str,
    line_num: int,
    vault_index: dict[str, Path] | None,
) -> list[LintError]:
    errors: list[LintError] = []
    i = 0
    n = len(line)

    while i < n:
        # Skip escaped characters
        if line[i] == "\\":
            i += 2
            continue

        # Skip embeds  ![[...]]  — handled by the embeds module
        if line[i : i + 3] == "![[":
            i += 3
            # Fast-forward past this embed's closing ]] (if any)
            while i < n:
                if line[i : i + 2] == "]]":
                    i += 2
                    break
                i += 1
            continue

        # Wikilink opening  [[
        if line[i : i + 2] == "[[":
            open_pos = i
            i += 2
            content_start = i

            # Scan for the matching ]]
            while i < n:
                if line[i : i + 2] == "]]":
                    content = line[content_start:i]
                    i += 2
                    _validate_wikilink(
                        content, line_num, open_pos, vault_index, errors
                    )
                    break
                i += 1
            else:
                # Reached end of line without ]]
                errors.append(
                    LintError(
                        rule="unclosed-wikilink",
                        severity=Severity.ERROR,
                        line=line_num,
                        message="Wikilink [[ is not closed with ]]",
                    )
                )
            continue

        i += 1

    return errors


def _validate_wikilink(
    content: str,
    line_num: int,
    open_pos: int,
    vault_index: dict[str, Path] | None,
    errors: list[LintError],
) -> None:
    """Validate the content of a closed wikilink."""
    if not content.strip():
        errors.append(
            LintError(
                rule="empty-wikilink",
                severity=Severity.ERROR,
                line=line_num,
                message="Wikilink [[]] is empty",
            )
        )
        return

    # Target is the part before the first | (alias separator)
    target = content.split("|")[0]

    # Validate character positions: multiple # is invalid
    if target.count("#") > 1:
        errors.append(
            LintError(
                rule="wikilink-invalid-chars",
                severity=Severity.ERROR,
                line=line_num,
                message=f"Wikilink target has multiple '#' characters: [[{content}]]",
            )
        )
        return

    # ^ must come after # (if both are present)
    if "#" in target and "^" in target:
        if target.index("^") < target.index("#"):
            errors.append(
                LintError(
                    rule="wikilink-invalid-chars",
                    severity=Severity.ERROR,
                    line=line_num,
                    message=f"Wikilink target has '^' before '#': [[{content}]]",
                )
            )
            return

    # broken-link check (WARNING, requires vault_path)
    if vault_index is not None:
        # Normalise: strip heading/block refs, strip alias
        note_name = target.split("#")[0].split("^")[0].strip()
        if note_name:  # non-empty: not a same-file heading link [[#heading]]
            if note_name.lower() not in vault_index:
                errors.append(
                    LintError(
                        rule="broken-link",
                        severity=Severity.WARNING,
                        line=line_num,
                        message=f"Link [[{content}]] does not resolve to an existing note",
                    )
                )
