"""Obsidian compatibility rules — standard Markdown constructs that Obsidian
does not reliably support or ignores.

Rules
-----
std-internal-link   : [text](path.md) or [text](path/note) — use [[wikilink]] instead.
std-internal-image  : ![alt](local/path) — use ![[image.png]] instead.
std-reference-link  : [text][ref] usage or [ref]: url definition.
heading-no-space    : #Heading without a space — use # Heading.
indented-code-block : 4+ space indented line preceded by blank — use fenced ``` instead.
raw-html            : Raw HTML tags — not reliably rendered in Obsidian.
std-horizontal-rule : *** or ___ horizontal rule — use --- instead.
"""

from __future__ import annotations

import re

from ..models import LintError, Severity
from ..utils import get_frontmatter_end, is_in_code_block

# ---------------------------------------------------------------------------
# std-internal-link
# Matches [text](url) but NOT ![alt](url)  (images handled separately)
# ---------------------------------------------------------------------------
_MD_LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)")

_EXTERNAL_SCHEMES = re.compile(
    r"^(https?|ftp|mailto|tel|file|data):", re.IGNORECASE
)


def _is_internal_url(url: str) -> bool:
    url = url.strip()
    if _EXTERNAL_SCHEMES.match(url):
        return False
    if url.startswith("#"):        # same-page anchor
        return False
    if url.lower().endswith(".md"):
        return True
    if "/" in url:                 # relative path
        return True
    return False


# ---------------------------------------------------------------------------
# std-internal-image
# ---------------------------------------------------------------------------
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

_EXTERNAL_IMAGE_SCHEMES = re.compile(r"^(https?|data):", re.IGNORECASE)


def _is_local_image_url(url: str) -> bool:
    return not _EXTERNAL_IMAGE_SCHEMES.match(url.strip())


# ---------------------------------------------------------------------------
# std-reference-link
# [text][ref] usage  and  [ref]: url definition
# The def pattern excludes footnotes by requiring first char != ^
# ---------------------------------------------------------------------------
_REF_LINK_USE_RE = re.compile(r"(?<!!)\[([^\]]+)\]\[([^\]]*)\]")
_REF_LINK_DEF_RE = re.compile(r"^\s*\[([^\]^][^\]]*)\]:\s+\S")


# ---------------------------------------------------------------------------
# heading-no-space
# #Heading or ##Heading — first non-# char after the hashes is not whitespace
# Special case: single # followed by a single word with no spaces is likely
# an Obsidian tag, not a broken heading, so we skip it.
# ---------------------------------------------------------------------------
_HEADING_NO_SPACE_RE = re.compile(r"^(#{1,6})([^#\s].*)$")


def _check_heading_no_space(line: str, line_num: int) -> LintError | None:
    m = _HEADING_NO_SPACE_RE.match(line)
    if not m:
        return None
    hashes, text = m.group(1), m.group(2)
    # Single # + single word with no internal spaces → likely an Obsidian tag
    if len(hashes) == 1 and " " not in text:
        return None
    return LintError(
        rule="heading-no-space",
        severity=Severity.ERROR,
        line=line_num,
        message=f'Heading missing space after {hashes!r}: write "{hashes} {text}" instead',
    )


# ---------------------------------------------------------------------------
# indented-code-block
# A line with 4+ leading spaces preceded by a blank line.
# Lines whose stripped content starts with a list marker are skipped
# (they are list indentation, not code blocks).
# ---------------------------------------------------------------------------
_FOUR_SPACES_RE = re.compile(r"^    ")
_LIST_MARKER_RE = re.compile(r"^([-*+]|\d+[.)]) ")


def _preceded_by_blank(lines: list[str], i: int, fm_end: int) -> bool:
    """Return True if the line immediately before i (skipping code-block lines) is blank."""
    j = i - 1
    while j >= fm_end and is_in_code_block(lines, j):
        j -= 1
    if j < fm_end:
        return True   # first content line — treat as blank-preceded
    return lines[j].strip() == ""


# ---------------------------------------------------------------------------
# raw-html
# Matches opening/closing/self-closing tags whose name is a known HTML element.
# ---------------------------------------------------------------------------
_HTML_TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)(\s[^>]*)?\s*/?>")

_HTML_TAGS: frozenset[str] = frozenset(
    {
        "a", "abbr", "address", "article", "aside", "audio",
        "b", "blockquote", "body", "br", "button",
        "canvas", "caption", "cite", "code", "col", "colgroup",
        "data", "datalist", "dd", "del", "details", "dfn", "dialog",
        "div", "dl", "dt",
        "em", "embed",
        "fieldset", "figcaption", "figure", "footer", "form",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "head", "header", "hr", "html",
        "i", "iframe", "img", "input", "ins",
        "kbd", "label", "legend", "li", "link",
        "main", "map", "mark", "menu", "meta", "meter",
        "nav", "noscript",
        "object", "ol", "optgroup", "option", "output",
        "p", "picture", "pre", "progress",
        "q", "rp", "rt", "ruby",
        "s", "samp", "script", "section", "select", "small",
        "source", "span", "strong", "style", "sub", "summary", "sup",
        "table", "tbody", "td", "template", "textarea", "tfoot",
        "th", "thead", "time", "title", "tr", "track",
        "u", "ul",
        "var", "video",
        "wbr",
    }
)


# ---------------------------------------------------------------------------
# std-horizontal-rule
# Lines consisting only of *** / * * * / ___ / _ _ _
# --- (with or without spaces) is the Obsidian-reliable form and is not flagged.
# ---------------------------------------------------------------------------
_STD_HR_RE = re.compile(r"^\s*((\*\s*){3,}|(_\s*){3,})\s*$")


# ---------------------------------------------------------------------------
# Main check function
# ---------------------------------------------------------------------------

def check(lines: list[str], vault_path: str | None = None) -> list[LintError]:
    errors: list[LintError] = []
    fm_end = get_frontmatter_end(lines)

    for i, line in enumerate(lines):
        if i < fm_end:
            continue
        if is_in_code_block(lines, i):
            continue

        line_num = i + 1

        # -- std-internal-link -----------------------------------------------
        for m in _MD_LINK_RE.finditer(line):
            url = m.group(2)
            if _is_internal_url(url):
                errors.append(
                    LintError(
                        rule="std-internal-link",
                        severity=Severity.ERROR,
                        line=line_num,
                        message=(
                            f"Standard Markdown link to internal note "
                            f"[{m.group(1)}]({url}); use [[wikilink]] instead"
                        ),
                    )
                )

        # -- std-internal-image -----------------------------------------------
        for m in _MD_IMAGE_RE.finditer(line):
            url = m.group(2)
            if _is_local_image_url(url):
                filename = url.rsplit("/", 1)[-1]
                errors.append(
                    LintError(
                        rule="std-internal-image",
                        severity=Severity.ERROR,
                        line=line_num,
                        message=(
                            f"Standard Markdown image with local path "
                            f"![{m.group(1)}]({url}); use ![[{filename}]] instead"
                        ),
                    )
                )

        # -- std-reference-link (usage) ---------------------------------------
        for m in _REF_LINK_USE_RE.finditer(line):
            errors.append(
                LintError(
                    rule="std-reference-link",
                    severity=Severity.ERROR,
                    line=line_num,
                    message=(
                        f"Reference-style link [{m.group(1)}][{m.group(2)}] "
                        "is not supported in Obsidian; use [[wikilink]] instead"
                    ),
                )
            )

        # -- std-reference-link (definition) ----------------------------------
        m = _REF_LINK_DEF_RE.match(line)
        if m:
            errors.append(
                LintError(
                    rule="std-reference-link",
                    severity=Severity.ERROR,
                    line=line_num,
                    message=(
                        f"Reference link definition [{m.group(1)}]: "
                        "is not supported in Obsidian"
                    ),
                )
            )

        # -- heading-no-space -------------------------------------------------
        err = _check_heading_no_space(line, line_num)
        if err:
            errors.append(err)

        # -- indented-code-block ----------------------------------------------
        if _FOUR_SPACES_RE.match(line):
            content = line.lstrip()
            if (
                not _LIST_MARKER_RE.match(content)
                and _preceded_by_blank(lines, i, fm_end)
            ):
                errors.append(
                    LintError(
                        rule="indented-code-block",
                        severity=Severity.ERROR,
                        line=line_num,
                        message=(
                            "Indented code block (4+ spaces) is not rendered by "
                            "Obsidian; use a fenced ``` block instead"
                        ),
                    )
                )

        # -- raw-html ---------------------------------------------------------
        for m in _HTML_TAG_RE.finditer(line):
            if m.group(2).lower() in _HTML_TAGS:
                errors.append(
                    LintError(
                        rule="raw-html",
                        severity=Severity.ERROR,
                        line=line_num,
                        message=(
                            f"Raw HTML <{m.group(2)}> is not reliably rendered "
                            "in Obsidian; use Markdown formatting instead"
                        ),
                    )
                )
                break  # one error per line is enough

        # -- std-horizontal-rule ----------------------------------------------
        if _STD_HR_RE.match(line):
            char = "*" if "*" in line.strip() else "_"
            errors.append(
                LintError(
                    rule="std-horizontal-rule",
                    severity=Severity.ERROR,
                    line=line_num,
                    message=(
                        f"Horizontal rule using '{char}' is not reliable in "
                        "Obsidian; use --- instead"
                    ),
                )
            )

    return errors
