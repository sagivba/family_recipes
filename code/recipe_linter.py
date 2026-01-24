# recipe_linter.py – enhanced with human-readable pretty front-matter errors

import os
import re
import yaml
import click
import difflib
from typing import Dict, List, Tuple

# =====================
# Configuration
# =====================

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

# =====================
# Front-matter syntax checks (no YAML parser)
# =====================

COLON_NO_SPACE_RE = re.compile(r'^([A-Za-z0-9_]+):(\S)')
MISSING_CLOSE_QUOTE_RE = re.compile(r'^[A-Za-z0-9_]+:\s*"[^"\n]*$')
MISSING_OPEN_QUOTE_RE = re.compile( r'^[A-Za-z0-9_]+:\s+[^"\s].*"$')

INNER_COLON_UNQUOTED_RE = re.compile(r'^[A-Za-z0-9_]+:\s*[^"\n]*:[^"\n]*$')


def shorten_line(line: str) -> str:
    words = line.split()
    if len(words) <= 6:
        return line
    return f"{' '.join(words[:3])} ... {' '.join(words[-3:])}"


def pretty_print_front_matter(fm_lines: List[str]) -> Dict:
    lines = []
    errors = []
    err_no = 1

    lines.append("START\t\t---")

    for idx, raw in enumerate(fm_lines, start=1):
        raw = raw.rstrip("\n")
        stripped = raw.strip()

        if not stripped:
            continue

        status = "OK"
        message = None

        if COLON_NO_SPACE_RE.match(stripped): message = "missing space after ':'"
        elif INNER_COLON_UNQUOTED_RE.match(stripped): message = "value contains ':' and must be quoted"
        elif MISSING_CLOSE_QUOTE_RE.match(stripped):  message = 'missing " at the end of line'
        elif MISSING_OPEN_QUOTE_RE.match(stripped): message = 'missing " at the beginning of value'


        if message:
            status = f"ERROR {err_no:02d}"
            lines.append(f"{status}\t{shorten_line(raw)}")
            errors.append({
                "code": err_no,
                "line": idx,
                "message": message
            })
            err_no += 1
        else:
            lines.append(f"OK\t\t{raw}")

    lines.append("END\t---")

    return {"lines": lines, "errors": errors}

# =====================
# Utilities
# =====================

def read_file(path: str) -> List[str]:
    with open(path, encoding="utf-8") as f:
        return f.readlines()

# =====================
# Front Matter extraction
# =====================

def extract_front_matter(lines: List[str]) -> Tuple[List[str], int, int]:
    if not lines or lines[0].strip() != "---":
        return [], -1, -1

    fm_lines = []
    end_idx = -1

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
        fm_lines.append(lines[i])

    return fm_lines, 1, end_idx

# =====================
# YAML semantic linting (only if syntax OK)
# =====================

def lint_front_matter_keys(front: Dict) -> List[Dict]:
    errors = []

    for key in REQUIRED_FRONT_FIELDS:
        if key not in front:
            errors.append(f"Missing required field '{key}'")

    for key in front:
        if key not in KNOWN_FIELDS:
            suggestion = difflib.get_close_matches(key, KNOWN_FIELDS, n=1)
            msg = f"Unknown field '{key}'"
            if suggestion:
                msg += f", did you mean '{suggestion[0]}'?"
            errors.append(msg)

    return errors

# =====================
# Sections
# =====================

def extract_sections(body_lines: List[str]) -> List[str]:
    return [line.strip() for line in body_lines if line.strip().startswith('#')]


def validate_sections(found: List[str]) -> List[str]:
    if found != REQUIRED_SECTIONS:
        return [
            "Invalid section order",
            f"Expected: {REQUIRED_SECTIONS}",
            f"Found:    {found}",
        ]
    return []

# =====================
# Lint File
# =====================

def lint_recipe(path: str) -> bool:
    lines = read_file(path)

    fm_lines, start, end = extract_front_matter(lines)
    if end == -1:
        return True

    pretty = pretty_print_front_matter(fm_lines)
    if pretty['errors']:
        print(f"\nFile: {path}")
        for l in pretty['lines']:
            print(l)
        for e in pretty['errors']:
            print(f"\nError {e['code']:02d}:\n\t{e['message']}")
        return False

    # YAML is now safe
    front = yaml.safe_load(''.join(fm_lines)) or {}

    key_errors = lint_front_matter_keys(front)
    section_errors = validate_sections(extract_sections(lines[end + 1:]))

    if key_errors or section_errors:
        print(f"\nFile: {path}")
        for e in key_errors + section_errors:
            print(f"ERROR\t{e}")
        return False

    return True

# =====================
# Directory
# =====================

def lint_directory(recipes_dir: str) -> None:
    ok, bad = 0, 0
    for file in os.listdir(recipes_dir):
        if not file.endswith('.md'):
            continue
        if lint_recipe(os.path.join(recipes_dir, file)):
            ok += 1
        else:
            bad += 1

    print(f"\nvalids:   {ok}")
    print(f"invalids: {bad}")

# =====================
# CLI
# =====================

@click.command(help="""
Recipe Markdown Linter

This tool validates recipe Markdown files with YAML front matter.

What it checks:
1. YAML front matter syntax (before parsing YAML):
   - Missing space after ':'
   - Missing opening or closing quotes
   - Unquoted values containing ':'
   - Reports line-by-line OK / ERROR with clear messages

2. YAML semantic validation (only if syntax is clean):
   - Required fields exist (layout, title, category, description)
   - Unknown fields (with suggestions)

3. Markdown structure:
   - Required sections exist
   - Sections appear in the exact required order

Behavior:
- Pretty front-matter output is shown ONLY when syntax errors are found
- Files without errors produce no per-file output
- Final summary always shows number of valid / invalid files

Typical usage:
  recipe_linter.py recipes/
  recipe_linter.py recipes/ --no-pretty
  recipe_linter.py recipes/ --quiet
""")
@click.argument("recipes_directory", type=click.Path(exists=True, file_okay=False))
@click.option("--pretty/--no-pretty", default=True, help="Show pretty front-matter output when errors are found")
@click.option("--quiet", is_flag=True, help="Suppress all output except final summary")
def main(recipes_directory, pretty, quiet):
    lint_directory(recipes_directory)


if __name__ == '__main__':
    main()
