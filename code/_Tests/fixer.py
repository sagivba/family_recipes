"""
Recipe fixer.

This module applies safe, deterministic fixes to recipe markdown files
based on lint results.
"""

import re
from pathlib import Path
from typing import List, Optional


# ----------------------------
# Models
# ----------------------------

class FixAction:
    """
    Represents a single fix action applied to a file.
    """

    def __init__(self, description: str):
        self.description = description

    def __repr__(self) -> str:
        return f"FixAction(description={self.description!r})"


class FixResult:
    """
    Holds the result of applying fixes to a recipe file.
    """

    def __init__(
        self,
        path: Path,
        original: str,
        fixed: str,
        actions: List[FixAction],
    ):
        self.path = path
        self.original = original
        self.fixed = fixed
        self.actions = actions

    @property
    def changed(self) -> bool:
        return self.original != self.fixed


# ----------------------------
# Fix helpers
# ----------------------------

COLON_NO_SPACE_RE = re.compile(r'^([A-Za-z0-9_]+):(\S)', re.MULTILINE)


def _fix_colon_spacing(text: str, actions: List[FixAction]) -> str:
    def repl(match):
        actions.append(
            FixAction("Added missing space after ':' in front matter")
        )
        return f"{match.group(1)}: {match.group(2)}"

    return COLON_NO_SPACE_RE.sub(repl, text)


def _ensure_description(text: str, actions: List[FixAction]) -> str:
    lines = text.splitlines(keepends=True)

    if not lines or lines[0].strip() != "---":
        return text

    for line in lines:
        if line.startswith("description:"):
            return text

    # insert description before closing ---
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            lines.insert(
                i,
                'description: "TODO: add description"\n'
            )
            actions.append(
                FixAction("Added placeholder description field")
            )
            break

    return "".join(lines)


# ----------------------------
# Public API
# ----------------------------

def fix_recipe(path: Path) -> FixResult:
    """
    Apply safe fixes to a recipe markdown file.

    Args:
        path: Path to the recipe markdown file

    Returns:
        FixResult containing original content, fixed content,
        and a list of applied actions.
    """

    original = path.read_text(encoding="utf-8")
    fixed = original
    actions: List[FixAction] = []

    fixed = _fix_colon_spacing(fixed, actions)
    fixed = _ensure_description(fixed, actions)

    return FixResult(
        path=path,
        original=original,
        fixed=fixed,
        actions=actions,
    )
