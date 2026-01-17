import os
import re
import yaml
import click
from typing import List, Dict, Tuple


REQUIRED_FRONT_FIELDS = {
    "layout": "recipe",
    "title": None,
    "category": None,
}

OPTIONAL_FRONT_FIELDS = [
    "type",
    "origin",
    "spiciness",
    "diabetic_friendly",
    "image",
    "source",
    "notes",
]

REQUIRED_SECTIONS = [
    "DESCRIPTION",
    "## מצרכים",
    "## אופן ההכנה",
    "## ערכים תזונתיים (הערכה ל-100 גרם)",
    "### ויטמינים ומינרלים בולטים",
    "## הערות",
]


# ---------- File IO ----------
def read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------- Front matter ----------
def extract_front_matter(text: str) -> Tuple[Dict, str, List[str]]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not match:
        return {}, text, ["Missing YAML front matter"]

    front_raw, body = match.groups()
    try:
        front = yaml.safe_load(front_raw) or {}
    except yaml.YAMLError as e:
        return {}, body, [f"Invalid YAML: {e}"]

    return front, body, []


def validate_front_matter(front: Dict) -> List[str]:
    errors = []

    for field, expected in REQUIRED_FRONT_FIELDS.items():
        if field not in front:
            errors.append(f"Missing required field: {field}")
        elif expected and front[field] != expected:
            errors.append(f"Field '{field}' must be '{expected}'")

    for field in OPTIONAL_FRONT_FIELDS:
        if field not in front:
            errors.append(f"Missing optional field (must exist): {field}")

    return errors


# ---------- Sections ----------
def extract_sections(body: str) -> Tuple[List[str], bool]:
    lines = body.strip().splitlines()

    has_h1 = any(line.startswith("# ") for line in lines)
    headers = [line.strip() for line in lines if line.startswith("#")]

    description_exists = False
    for line in lines:
        if line.startswith("#"):
            break
        if line.strip():
            description_exists = True
            break

    sections = []
    if description_exists:
        sections.append("DESCRIPTION")

    sections.extend(headers)
    return sections, has_h1


def validate_sections(found: List[str]) -> List[str]:
    if found != REQUIRED_SECTIONS:
        return [
            "Sections missing or out of order",
            f"Expected: {REQUIRED_SECTIONS}",
            f"Found:    {found}",
        ]
    return []


# ---------- Linting ----------
def lint_recipe(path: str) -> Dict:
    result = {
        "file": path,
        "valid": True,
        "errors": [],
    }

    text = read_file(path)

    front, body, fm_errors = extract_front_matter(text)
    result["errors"].extend(fm_errors)

    if fm_errors:
        result["valid"] = False
        return result

    result["errors"].extend(validate_front_matter(front))

    sections, has_h1 = extract_sections(body)
    result["errors"].extend(validate_sections(sections))

    if has_h1:
        result["errors"].append("Extra H1 (#) header found in body")

    if result["errors"]:
        result["valid"] = False

    return result


def lint_directory(recipes_dir: str) -> Dict[str, List]:
    report = {
        "valid_files": [],
        "invalid_files": [],
    }

    for file in os.listdir(recipes_dir):
        if not file.endswith(".md"):
            continue

        full_path = os.path.join(recipes_dir, file)
        result = lint_recipe(full_path)

        if result["valid"]:
            report["valid_files"].append(file)
        else:
            report["invalid_files"].append(result)

    return report


# ---------- Report ----------
def write_report(report: Dict, output_path: str):
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n=== VALID FILES ===\n")
        for file in report["valid_files"]:
            f.write(f"  - {file}\n")
        print(f"valid: {len(report['valid_files'])}")

        f.write("\n=== INVALID FILES ===\n")
        for item in report["invalid_files"]:
            f.write(f"\nFile: {item['file']}\n")
            for err in item["errors"]:
                f.write(f"  * {err}\n")
        print(f"valid: {len(report['invalid_files'])}")


# ---------- CLI ----------
@click.command(
    help="""
Recipe Markdown Linter

Validates Markdown recipe files against a strict format contract
intended for use with a Jekyll-based recipe website.

WHAT IS CHECKED
---------------
For each `.md` recipe file:

1. YAML Front Matter
   - Must exist and be enclosed by '---'
   - Required fields:
       * layout (must be exactly "recipe")
       * title (non-empty)
       * category (non-empty)
   - Optional fields (must exist):
       * type, origin, spiciness, diabetic_friendly,
         image, source, notes

2. Recipe Body Structure
   - Sections must exist in this exact order:
       1. Short description (free text before any heading)
       2. ## מצרכים
       3. ## אופן ההכנה
       4. ## ערכים תזונתיים (הערכה ל-100 גרם)
       5. ### ויטמינים ומינרלים בולטים
       6. ## הערות

3. Markdown Rules
   - No H1 (#) headers allowed in the body

OUTPUT
------
Produces a human-readable report listing:
- Valid recipe files
- Invalid files with detailed errors

The script is read-only and never modifies recipe files.
"""
)
@click.argument(
    "recipes_directory",
    type=click.Path(exists=True, file_okay=False)
)
@click.argument(
    "output_file",
    type=click.Path(dir_okay=False)
)
def main(recipes_directory: str, output_file: str):
    report = lint_directory(recipes_directory)
    write_report(report, output_file)


if __name__ == "__main__":
    main()
