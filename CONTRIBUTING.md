# Contributing to mdlint-obsidian

Thank you for your interest in contributing!

## Adding a New Rule

1. **Pick the right module.** Rules are grouped by topic in `mdlint_obsidian/rules/`. Add your rule to the most relevant existing module, or create a new one if the topic is genuinely distinct.

2. **Implement the check.** Each rule module exposes a `check(lines, vault_path=None)` function that returns a list of `LintError` objects. Follow this pattern:

   ```python
   from ..models import LintError, Severity
   from ..utils import is_in_code_block, get_frontmatter_end

   def check(lines: list[str], vault_path=None) -> list[LintError]:
       errors = []
       fm_end = get_frontmatter_end(lines)
       for i, line in enumerate(lines):
           if i < fm_end:
               continue
           if is_in_code_block(lines, i):
               continue
           # ... your check logic ...
       return errors
   ```

3. **Name the rule in kebab-case.** Example: `my-new-rule`. Document it in the module docstring and add it to the rules table in `README.md`.

4. **Assign the right severity.** Use `Severity.ERROR` for structural problems that break rendering, and `Severity.WARNING` for issues that are valid in some contexts (e.g., custom CSS callout types, unresolved links when the vault root is unknown).

5. **Skip code blocks.** Call `is_in_code_block(lines, i)` for every line you inspect. This is the most important correctness requirement — content inside fences must never be flagged.

6. **Skip frontmatter.** Call `get_frontmatter_end(lines)` and skip lines before that index, unless your rule specifically applies to frontmatter.

7. **Write tests.** Add a test file `tests/test_<module>.py` (or add to an existing one). Every rule needs at minimum:
   - A test showing valid content produces no errors.
   - A test for each error condition that asserts the correct `rule` name and `line` number.
   - A test confirming the rule is silent when the violation is inside a code block.

8. **Register the module.** Import and call your module in `mdlint_obsidian/linter.py`'s `validate()` function.

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

**Coverage** — aim to keep rule module coverage at 95%+. Run:

```bash
pytest --cov=mdlint_obsidian --cov-report=term-missing
```

Current baseline: **89% overall** (135 tests). The CLI (`cli.py`) is intentionally excluded from the per-rule target — it has 0% coverage because it requires subprocess/integration tests. Expected uncovered areas:

| Module | Notes |
|--------|-------|
| `cli.py` | No unit tests; test manually or with subprocess integration tests |
| `models.py` | The `__eq__` override — covered implicitly but not via direct equality assertion |
| Rule branches | Conservative early-returns in `math.py`, YAML error line extraction in `frontmatter.py` |

## Code Style

- Python 3.10+, type hints on all public functions.
- Keep rule logic self-contained within its module.
- Prefer clarity over cleverness — these checks run on user notes, so false positives are worse than false negatives.
