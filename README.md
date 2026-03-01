# mdlint-obsidian

<!-- Badges placeholder -->
<!-- [![PyPI version](https://badge.fury.io/py/mdlint-obsidian.svg)](https://badge.fury.io/py/mdlint-obsidian) -->
<!-- [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) -->
<!-- [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) -->
<!-- [![Tests](https://github.com/you/mdlint-obsidian/actions/workflows/test.yml/badge.svg)](https://github.com/you/mdlint-obsidian/actions) -->

A Python library and CLI tool that lints **Obsidian Flavored Markdown** files.

It checks for structural problems — unclosed wikilinks, invalid frontmatter, malformed tables, unmatched math delimiters and more — so you catch issues before they cause broken renders in your vault.

---

## Installation

```bash
pip install mdlint-obsidian
```

Or with [pipx](https://pypa.github.io/pipx/) for an isolated CLI install:

```bash
pipx install mdlint-obsidian
```

---

## Usage

### CLI

```bash
# Lint a single file
mdlint path/to/note.md

# Lint an entire vault (all .md files recursively)
mdlint path/to/vault/

# Enable broken-link checking (requires vault root)
mdlint note.md --vault path/to/vault/

# Show only errors (suppress warnings)
mdlint note.md --severity error

# Machine-readable JSON output
mdlint note.md --format json
```

**Exit codes:** `0` if no errors (warnings alone do not fail), `1` if any errors are found.

**Example output (text format):**

```
notes/my-note.md:5: [ERROR] unclosed-wikilink: Wikilink [[ is not closed with ]]
notes/my-note.md:12: [WARNING] broken-link: Link [[Missing Note]] does not resolve to an existing note
```

**Example output (JSON format):**

```json
[
  {
    "file": "notes/my-note.md",
    "line": 5,
    "rule": "unclosed-wikilink",
    "severity": "error",
    "message": "Wikilink [[ is not closed with ]]"
  }
]
```

### Python library

```python
from mdlint_obsidian import validate, LintError, Severity

content = open("my-note.md").read()

# Basic validation
errors = validate(content)

# With vault path for broken-link checking
errors = validate(content, vault_path="/path/to/vault")

for error in errors:
    print(f"Line {error.line} [{error.severity.value.upper()}] {error.rule}: {error.message}")
```

The `validate()` function returns a list of `LintError` dataclass instances:

```python
@dataclass
class LintError:
    rule: str          # e.g. "unclosed-wikilink"
    severity: Severity # Severity.ERROR or Severity.WARNING
    line: int          # 1-indexed line number
    message: str
```

**Filtering by severity:**

```python
from mdlint_obsidian import validate, Severity

errors = validate(content)
errors_only = [e for e in errors if e.severity == Severity.ERROR]
warnings_only = [e for e in errors if e.severity == Severity.WARNING]
```

---

## Rules

All rules skip content inside fenced code blocks (``` ` ``` `` or `~~~`).

### Frontmatter

| Rule | Severity | Description |
|------|----------|-------------|
| `frontmatter-not-first` | ERROR | A `---...---` block that parses as YAML frontmatter exists but does not start at line 1 |
| `frontmatter-invalid-yaml` | ERROR | The frontmatter block cannot be parsed as valid YAML |
| `frontmatter-unclosed` | ERROR | An opening `---` at line 1 has no closing `---` |

### Wikilinks

| Rule | Severity | Description |
|------|----------|-------------|
| `unclosed-wikilink` | ERROR | `[[` without a matching `]]` |
| `empty-wikilink` | ERROR | `[[]]` with no content |
| `wikilink-invalid-chars` | ERROR | Wikilink target contains `#` or `^` in invalid positions (e.g. multiple `#`, or `^` before `#`) |
| `broken-link` | WARNING | `[[Note Name]]` does not resolve to an existing `.md` file in the vault (only when `--vault` is provided) |

### Embeds

| Rule | Severity | Description |
|------|----------|-------------|
| `unclosed-embed` | ERROR | `![[` without a matching `]]` |
| `empty-embed` | ERROR | `![[]]` with no content |
| `embed-invalid-dimension` | ERROR | `![[file\|WxH]]` where the dimension suffix is malformed (e.g. `300x` or `x200`) |

### Callouts

| Rule | Severity | Description |
|------|----------|-------------|
| `callout-invalid-type` | WARNING | `> [!type]` where type is not one of the 13 built-in Obsidian types or their aliases (custom CSS types are valid, hence warning) |
| `callout-missing-continuation` | ERROR | The line immediately after a callout header is non-empty and does not start with `>` |
| `callout-invalid-modifier` | ERROR | The modifier after the callout type is not `+` or `-` |

**Built-in callout types:** `note`, `abstract`/`summary`/`tldr`, `info`, `todo`, `tip`/`hint`/`important`, `success`/`check`/`done`, `question`/`help`/`faq`, `warning`/`caution`/`attention`, `failure`/`fail`/`missing`, `danger`/`error`, `bug`, `example`, `quote`/`cite`

### Code Blocks

| Rule | Severity | Description |
|------|----------|-------------|
| `unclosed-code-block` | ERROR | An opening fence (`` ``` `` or `~~~`) has no matching closing fence |

### Formatting

| Rule | Severity | Description |
|------|----------|-------------|
| `unclosed-highlight` | ERROR | `==` opened but not closed on the same line |
| `unclosed-comment` | ERROR | `%%` opened but never closed (document-level) |

### Footnotes

| Rule | Severity | Description |
|------|----------|-------------|
| `orphaned-footnote-ref` | ERROR | `[^id]` reference in the body with no matching `[^id]:` definition |
| `orphaned-footnote-def` | ERROR | `[^id]:` definition with no matching `[^id]` reference in the body |

### Tables

| Rule | Severity | Description |
|------|----------|-------------|
| `table-missing-separator` | ERROR | Table header row is not followed by a separator row (`\|---|`) |
| `table-inconsistent-columns` | ERROR | A table body row has a different column count than the header |

### Math

| Rule | Severity | Description |
|------|----------|-------------|
| `unclosed-math-block` | ERROR | `$$` block opened but never closed (document-level) |
| `unclosed-inline-math` | WARNING | `$` opened but not closed on the same line (conservative: ignores `$100`-style currency) |

---

## Development

```bash
git clone https://github.com/you/mdlint-obsidian.git
cd mdlint-obsidian
pip install -e ".[dev]"
pytest
pytest --cov=mdlint_obsidian --cov-report=term-missing
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for information on adding new rules.

---

## License

MIT — see [LICENSE](LICENSE).
