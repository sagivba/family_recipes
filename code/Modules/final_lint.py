from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - environment fallback
    yaml = None

REQUIRED_FRONT_FIELDS = [
    "layout",
    "title",
    "category",
    "description",
]

KNOWN_FIELDS = REQUIRED_FRONT_FIELDS + [
    "type",
    "origin",
    "spiciness",
    "diabetic_friendly",
    "image",
    "source",
    "notes",
    "author",
    "yield",
]

REQUIRED_SECTIONS = [
    "## מצרכים",
    "## אופן ההכנה",
    "## ערכים תזונתיים (הערכה ל-100 גרם)",
    "### ויטמינים ומינרלים בולטים",
    "## הערות",
]

COLON_NO_SPACE_RE = re.compile(r"^([A-Za-z0-9_]+):(\S)")
MISSING_CLOSE_QUOTE_RE = re.compile(r'^[A-Za-z0-9_]+:\s*"[^"\n]*$')
MISSING_OPEN_QUOTE_RE = re.compile(r'^[A-Za-z0-9_]+:\s+[^"\s].*"$')
INNER_COLON_UNQUOTED_RE = re.compile(r'^[A-Za-z0-9_]+:\s*[^"\n]*:[^"\n]*$')


@dataclass(frozen=True)
class LintIssue:
    kind: str
    code: str | None
    message: str
    line: int | None
    column: int | None


@dataclass
class LintReport:
    ok: bool
    issues: list[LintIssue] = field(default_factory=list)
    pretty_lines: list[str] = field(default_factory=list)

    def sorted_issues(self) -> list[LintIssue]:
        def key(issue: LintIssue) -> tuple[int, int, str, str]:
            return (
                issue.line if issue.line is not None else -1,
                issue.column if issue.column is not None else -1,
                issue.code or "",
                issue.message,
            )

        return sorted(self.issues, key=key)

    def __str__(self) -> str:
        lines = [f"ok={self.ok}"]
        for issue in self.sorted_issues():
            where = f"{issue.line if issue.line is not None else '-'}:{issue.column if issue.column is not None else '-'}"
            lines.append(
                f"{issue.kind}|{issue.code or '-'}|{where}|{issue.message}"
            )

        if self.pretty_lines:
            lines.append("pretty:")
            lines.extend(self.pretty_lines)

        return "\n".join(lines)


class finallint:
    def lint_text(self, text: str, *, virtual_path: str = "<memory>") -> LintReport:
        del virtual_path
        lines = text.splitlines(keepends=True)

        fm_lines, _, end = _extract_front_matter(lines)
        if end == -1:
            return LintReport(ok=True, issues=[], pretty_lines=[])

        pretty_result = _pretty_front_matter(fm_lines)
        syntax_issues = pretty_result["issues"]
        if syntax_issues:
            report = LintReport(ok=False, issues=syntax_issues, pretty_lines=pretty_result["lines"])
            report.issues = report.sorted_issues()
            return report

        issues: list[LintIssue] = []

        front, parse_error = _parse_front_matter(fm_lines)
        if parse_error:
            issues.append(
                LintIssue(
                    kind="front_matter_semantic",
                    code="E_FM_YAML",
                    message=parse_error,
                    line=None,
                    column=None,
                )
            )
            return LintReport(ok=False, issues=issues, pretty_lines=[])

        if not isinstance(front, dict):
            issues.append(
                LintIssue(
                    kind="front_matter_semantic",
                    code="E_FM_NOT_MAP",
                    message="Front matter must be a YAML mapping",
                    line=None,
                    column=None,
                )
            )
            return LintReport(ok=False, issues=issues, pretty_lines=[])

        issues.extend(_lint_front_matter_semantics(front))
        issues.extend(_lint_sections(lines[end + 1 :]))

        report = LintReport(ok=not issues, issues=issues, pretty_lines=[])
        report.issues = report.sorted_issues()
        return report


def _shorten_line(line: str) -> str:
    words = line.split()
    if len(words) <= 6:
        return line
    return f"{' '.join(words[:3])} ... {' '.join(words[-3:])}"


def _extract_front_matter(lines: list[str]) -> tuple[list[str], int, int]:
    if not lines or lines[0].strip() != "---":
        return [], -1, -1

    fm_lines: list[str] = []
    end_idx = -1

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
        fm_lines.append(lines[i])

    return fm_lines, 1, end_idx


def _pretty_front_matter(fm_lines: list[str]) -> dict[str, Any]:
    lines: list[str] = []
    issues: list[LintIssue] = []

    lines.append("START\t\t---")

    for idx, raw in enumerate(fm_lines, start=1):
        raw = raw.rstrip("\n")
        stripped = raw.strip()

        if not stripped:
            continue

        message = None
        code = None
        column = None

        if match := COLON_NO_SPACE_RE.match(stripped):
            message = "missing space after ':'"
            code = "E_FM_SPACE"
            column = match.start(2) + 1
        elif INNER_COLON_UNQUOTED_RE.match(stripped):
            message = "value contains ':' and must be quoted"
            code = "E_FM_QUOTE_COLON"
            column = stripped.find(":") + 1
        elif MISSING_CLOSE_QUOTE_RE.match(stripped):
            message = 'missing " at the end of line'
            code = "E_FM_QUOTE_CLOSE"
            column = len(stripped) + 1
        elif MISSING_OPEN_QUOTE_RE.match(stripped):
            message = 'missing " at the beginning of value'
            code = "E_FM_QUOTE_OPEN"
            first_non_space = len(stripped.split(":", maxsplit=1)[0]) + 2
            column = first_non_space

        if message:
            err_no = len(issues) + 1
            lines.append(f"ERROR {err_no:02d}\t{_shorten_line(raw)}")
            issues.append(
                LintIssue(
                    kind="front_matter_syntax",
                    code=code,
                    message=message,
                    line=idx,
                    column=column,
                )
            )
        else:
            lines.append(f"OK\t\t{raw}")

    lines.append("END\t---")

    return {"lines": lines, "issues": issues}


def _lint_front_matter_semantics(front: dict[str, Any]) -> list[LintIssue]:
    issues: list[LintIssue] = []

    for key in REQUIRED_FRONT_FIELDS:
        if key not in front:
            issues.append(
                LintIssue(
                    kind="front_matter_semantic",
                    code="E_FM_REQUIRED_FIELD",
                    message=f"Missing required field '{key}'",
                    line=None,
                    column=None,
                )
            )

    for key in front:
        if key not in KNOWN_FIELDS:
            suggestion = difflib.get_close_matches(key, KNOWN_FIELDS, n=1)
            msg = f"Unknown field '{key}'"
            if suggestion:
                msg += f", did you mean '{suggestion[0]}'?"
            issues.append(
                LintIssue(
                    kind="front_matter_semantic",
                    code="E_FM_UNKNOWN_FIELD",
                    message=msg,
                    line=None,
                    column=None,
                )
            )

    return issues


def _parse_front_matter(fm_lines: list[str]) -> tuple[Any, str | None]:
    blob = "".join(fm_lines)

    if yaml is not None:
        try:
            return (yaml.safe_load(blob) or {}), None
        except Exception as exc:  # pragma: no cover - parser-specific path
            return None, f"Invalid YAML front matter: {exc}"

    parsed: dict[str, str] = {}
    for idx, raw in enumerate(fm_lines, start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        if ":" not in stripped:
            return None, f"Invalid YAML front matter: invalid line {idx}"
        key, value = stripped.split(":", maxsplit=1)
        parsed[key.strip()] = value.strip().strip('"')

    return parsed, None


def _extract_sections(body_lines: list[str]) -> list[str]:
    return [line.strip() for line in body_lines if line.strip().startswith("#")]


def _lint_sections(body_lines: list[str]) -> list[LintIssue]:
    found = _extract_sections(body_lines)
    if found != REQUIRED_SECTIONS:
        return [
            LintIssue(
                kind="sections",
                code="E_SEC_ORDER",
                message="Invalid section order",
                line=None,
                column=None,
            ),
            LintIssue(
                kind="sections",
                code="E_SEC_EXPECTED",
                message=f"Expected: {REQUIRED_SECTIONS}",
                line=None,
                column=None,
            ),
            LintIssue(
                kind="sections",
                code="E_SEC_FOUND",
                message=f"Found:    {found}",
                line=None,
                column=None,
            ),
        ]
    return []
