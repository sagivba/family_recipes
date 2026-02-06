"""
Recipe markdown linter.

This module validates recipe files for:
- YAML front matter syntax
- Required front matter fields
- Required section headers and order
"""

import re
from pathlib import Path
from typing import List, Optional
import yaml


# ----------------------------
# Models
# ----------------------------

class LintIssue:
    """
    Represents a single lint issue found in a recipe file.
    """

    def __init__(self, message: str, line: Optional[int] = None):
        self.message = message
        self.line = line

    def __repr__(self) -> str:
        return f"LintIssue(message={self.message!r}, line={self.line})"


class LintResult:
    """
    Holds the result of linting a recipe file.
    """

    def __init__(self, path: Path):
        self.path = path
        self.issues: List[LintIssue] = []

    @property
    def is_valid(self) -> bool:
        return not self.issues


# ----------------------------
# Constants
# ----------------------------

REQUIRED_FRONT_FIELDS = [
    "layout",
    "title",
    "category",
    "description",
]

REQUIRED_SECTIONS = [
    "## מצרכים",
    "## אופן ההכנה",
    "## ערכים תזונתיים (הערכה ל-100 גרם)",
    "### ויטמינים ומינרלים בולטים",
    "## הערות",
]

FRONT_DELIM = "---"


# ----------------------------
# Front matter helpers
# ----------------------------

COLON_NO_SPACE_RE = re.compile(r'^([A-Za-z0-9_]+):(\S)')


def _extract_front_matter(lines: List[str]) -> tuple[list[str], int, int]:
    if not lines or lines[0].strip() != FRONT_DELIM:
        return [], -1, -1

    fm_lines = []
    for i in range(1, len(lines)):
        if lines[i].strip() == FRONT_DELIM:
            return fm_lines, 1, i
        fm_lines.append(lines[i])

    return [], -1, -1


def _lint_front_matter_syntax(
    fm_lines: List[str],
    result: LintResult,
) -> None:
    for idx, raw in enumerate(fm_lines, start=1):
        line = raw.strip()
        if not line:
            continue

        if COLON_NO_SPACE_RE.match(line):
            result.issues.append(
                LintIssue(
                    "Missing space after ':' in front matter",
                    line=idx,
                )
            )


def _lint_front_matter_semantics(
    fm_lines: List[str],
    result: LintResult,
) -> None:
    try:
        data = yaml.safe_load("".join(fm_lines)) or {}
    except Exception as exc:
        result.issues.append(
            LintIssue(f"Invalid YAML front matter: {exc}")
        )
        return

    for field in REQUIRED_FRONT_FIELDS:
        if field not in data:
            result.issues.append(
                LintIssue(f"Missing required front matter field: '{field}'")
            )


# ----------------------------
# Section helpers
# ----------------------------

def _extract_sections(lines: List[str]) -> List[str]:
    return [line.strip() for line in lines if line.strip().startswith("#")]


def _lint_sections(
    body_lines: List[str],
    result: LintResult,
) -> None:
    found = _extract_sections(body_lines)

    if found != REQUIRED_SECTIONS:
        result.issues.append(
            LintIssue(
                "Invalid section order or missing sections"
            )
        )


# ----------------------------
# Public API
# ----------------------------
def lint_recipe(path: Path) -> LintResult:
    """
    Lint a single recipe markdown file.
    """

    result = LintResult(path)

    try:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except Exception as exc:
        result.issues.append(
            LintIssue(f"Failed to read file: {exc}")
        )
        return result

    fm_lines, start, end = _extract_front_matter(lines)

    if start == -1:
        result.issues.append(
            LintIssue("Missing YAML front matter")
        )
        return result

    _lint_front_matter_syntax(fm_lines, result)
    _lint_front_matter_semantics(fm_lines, result)

    body_lines = lines[end + 1 :]
    _lint_sections(body_lines, result)

    return result
