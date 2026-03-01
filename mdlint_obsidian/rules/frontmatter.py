"""Frontmatter rules.

Rules
-----
frontmatter-not-first     : A ---...--- block that looks like YAML frontmatter
                            exists but does not start at line 1.
frontmatter-invalid-yaml  : The frontmatter block cannot be parsed as valid YAML.
frontmatter-unclosed      : An opening --- at line 1 has no closing ---.
"""

from __future__ import annotations

import yaml

from ..models import LintError, Severity


def check(lines: list[str], vault_path: str | None = None) -> list[LintError]:
    errors: list[LintError] = []

    if not lines:
        return errors

    # --- Case 1: file starts with --- (frontmatter in correct position) ---
    if lines[0].strip() == "---":
        close_idx: int | None = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                close_idx = i
                break

        if close_idx is None:
            errors.append(
                LintError(
                    rule="frontmatter-unclosed",
                    severity=Severity.ERROR,
                    line=1,
                    message="Frontmatter block has no closing ---",
                )
            )
            return errors

        yaml_content = "\n".join(lines[1:close_idx])
        try:
            yaml.safe_load(yaml_content)
        except yaml.YAMLError as exc:
            err_line = 2  # default: line after opening ---
            if hasattr(exc, "problem_mark") and exc.problem_mark is not None:
                err_line = exc.problem_mark.line + 2  # +1 for 0-index, +1 for opening
            errors.append(
                LintError(
                    rule="frontmatter-invalid-yaml",
                    severity=Severity.ERROR,
                    line=err_line,
                    message=f"Frontmatter YAML is invalid: {exc}",
                )
            )
        return errors

    # --- Case 2: file does NOT start with --- ---
    # Scan for the first ---...--- block that contains a YAML mapping.
    # If found, report it as misplaced frontmatter.
    i = 0
    while i < len(lines):
        if lines[i].strip() == "---":
            start_idx = i
            # Look for closing ---
            j = i + 1
            while j < len(lines):
                if lines[j].strip() == "---":
                    yaml_content = "\n".join(lines[i + 1 : j])
                    try:
                        parsed = yaml.safe_load(yaml_content)
                        if isinstance(parsed, dict) and parsed:
                            errors.append(
                                LintError(
                                    rule="frontmatter-not-first",
                                    severity=Severity.ERROR,
                                    line=start_idx + 1,
                                    message="Frontmatter block must start at line 1",
                                )
                            )
                    except yaml.YAMLError:
                        pass
                    break
                j += 1
            break  # only inspect the first --- occurrence
        i += 1

    return errors
