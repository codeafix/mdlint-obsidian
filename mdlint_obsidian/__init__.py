"""obsidian-linter: lint Obsidian Flavored Markdown files."""

from .linter import validate
from .models import LintError, Severity

__all__ = ["validate", "LintError", "Severity"]
