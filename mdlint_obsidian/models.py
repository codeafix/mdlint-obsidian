from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class LintError:
    rule: str
    severity: Severity
    line: int
    message: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LintError):
            return NotImplemented
        return (
            self.rule == other.rule
            and self.severity == other.severity
            and self.line == other.line
            and self.message == other.message
        )
