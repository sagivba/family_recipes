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

COLON_NO_SPACE_RE = re.compile(r"^([A-Za-z0-9_]+):(\S)")
INNER_COLON_UNQUOTED_RE = re.compile(r"^[A-Za-z0-9_]+:\s*[^\"']*:[^\"']*$")


# =====================
# Utilities
# =====================

def read_file(path: str) -> List[str]:
    with open(path, encoding="utf-8") as f:
        return f.readlines()


def is_quoted(value: str) -> bool:
    value = value.strip()
    return (
        (value.startswith('"') and value.endswith('"')) or
        (value.startswith("'") and value.endswith("'"))
    )


# =====================
# Front Matter
# =====================

def extract_front_matter(lines: List[str]) -> Tuple[List[str], int, int, List[Dict]]:
    if not lines or lines[0].strip() != "---":
        return [], -1, -1, [{
            "line": 1,
            "type": "MissingFrontMatter",
            "message": "Missing YAML front matter opening '---'"
        }]

    fm_lines = []
    errors = []
    end_idx = -1

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
        fm_lines.append(lines[i])

    if end_idx == -1:
        errors.append({
            "line": 1,
            "type": "MissingFrontMatterEnd",
            "message": "Missing YAML front matter closing '---'"
        })

    return fm_lines, 1, end_idx, errors


def lint_front_matter_raw(fm_lines: List[str]) -> List[Dict]:
    errors = []

    for idx, line in enumerate(fm_lines, start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if COLON_NO_SPACE_RE.match(stripped):
            key = stripped.split(":")[0]
            errors.append({
                "line": idx,
                "type": "MissingSpaceAfterColon",
                "message": f"Missing space after ':' in key '{key}'",
                "autofix": "Insert space after ':'"
            })

        if INNER_COLON_UNQUOTED_RE.match(stripped):
            key, value = stripped.split(":", 1)
            if not is_quoted(value):
                errors.append({
                    "line": idx,
                    "type": "UnquotedTextWithColon",
                    "message": f"Value for '{key}' contains ':' and must be quoted",
                    "autofix": "Wrap value in quotes"
                })

    return errors


def parse_front_matter_yaml(fm_lines: List[str]) -> Tuple[Dict, List[Dict]]:
    raw = "".join(fm_lines)
    try:
        return yaml.safe_load(raw) or {}, []
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        return {}, [{
            "line": (mark.line + 1) if mark else 1,
            "type": "InvalidYAML",
            "message": str(e)
        }]


def lint_front_matter_keys(front: Dict) -> List[Dict]:
    errors = []

    for key in REQUIRED_FRONT_FIELDS:
        if key not in front:
            errors.append({
                "line": 1,
                "type": "MissingRequiredField",
                "message": f"Missing required field '{key}'"
            })

    for key in front:
        if key not in KNOWN_FIELDS:
            suggestions = difflib.get_close_matches(key, KNOWN_FIELDS, n=1)
            msg = f"Unknown field '{key}'"
            if suggestions:
                msg += f", did you mean '{suggestions[0]}'?"
            errors.append({
                "line": 1,
                "type": "UnknownField",
                "message": msg
            })

    return errors


# =====================
# Sections
# =====================

def extract_sections(body_lines: List[str]) -> List[str]:
    return [line.strip() for line in body_lines if line.strip().startswith("#")]


def validate_sections(found: List[str]) -> List[Dict]:
    if found != REQUIRED_SECTIONS:
        return [{
            "line": 0,
            "type": "InvalidSectionOrder",
            "message": "Sections missing or out of order",
            "expected": REQUIRED_SECTIONS,
            "found": found
        }]
    return []


# =====================
# Lint File
# =====================

def lint_recipe(path: str) -> Dict:
    lines = read_file(path)
    report = {
        "file": path,
        "errors": []
    }

    fm_lines, start, end, fm_errors = extract_front_matter(lines)
    report["errors"].extend(fm_errors)

    if end == -1:
        return report

    report["errors"].extend(lint_front_matter_raw(fm_lines))

    front, yaml_errors = parse_front_matter_yaml(fm_lines)
    report["errors"].extend(yaml_errors)

    if front:
        report["errors"].extend(lint_front_matter_keys(front))

    body_lines = lines[end + 1:]
    found_sections = extract_sections(body_lines)
    report["errors"].extend(validate_sections(found_sections))

    return report


# =====================
# Directory
# =====================

def lint_directory(recipes_dir: str) -> List[Dict]:
    results = []
    for file in os.listdir(recipes_dir):
        if file.endswith(".md"):
            results.append(
                lint_recipe(os.path.join(recipes_dir, file))
            )
    return results


# =====================
# Report
# =====================

def write_report(results: List[Dict], output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        valids,invalids=0,0
        for item in results:
            if not item["errors"]:
                valids+=1
                continue

            invalids+=1
            f.write(f"\nFile: {item['file']}\n")
            for err in item["errors"]:
                line = err.get("line", "?")
                f.write(f"  Line {line} | {err['type']} | {err['message']}\n")
                if "expected" in err:
                    f.write(f"    Expected: {err['expected']}\n")
                    f.write(f"    Found:    {err['found']}\n")
                if "autofix" in err:
                    f.write(f"    Suggestion: {err['autofix']}\n")
        print(f"valids:   {valids}")
        print(f"invalids: {invalids}")


# =====================
# CLI
# =====================

@click.command()
@click.argument("recipes_directory", type=click.Path(exists=True, file_okay=False))
@click.argument("output_file", type=click.Path())
def main(recipes_directory, output_file):
    results = lint_directory(recipes_directory)
    write_report(results, output_file)


if __name__ == "__main__":
    main()
