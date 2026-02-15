"""YAML frontmatter parsing utilities."""

from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


class FrontmatterParseError(Exception):
    """Raised when frontmatter YAML cannot be parsed."""


def _fallback_parse_yaml(yaml_blob: str) -> dict:
    """Very small YAML subset parser for key/value and simple lists."""

    result = {}
    lines = yaml_blob.splitlines()
    idx = 0
    while idx < len(lines):
        raw = lines[idx]
        line = raw.strip()
        idx += 1
        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            raise FrontmatterParseError(f"Invalid YAML line: {raw}")

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value == "":
            items = []
            while idx < len(lines):
                next_line = lines[idx]
                if next_line.strip().startswith("- "):
                    items.append(next_line.strip()[2:].strip())
                    idx += 1
                elif not next_line.strip():
                    idx += 1
                else:
                    break
            result[key] = items
            continue

        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                result[key] = []
            else:
                result[key] = [v.strip().strip('"').strip("'") for v in inner.split(",")]
            continue

        if value.lower() in {"true", "false"}:
            result[key] = value.lower() == "true"
            continue

        result[key] = value.strip('"').strip("'")

    return result


def parse_frontmatter_text(text: str):
    """Parse YAML frontmatter from text.

    Returns:
        tuple[dict | None, str]: parsed frontmatter and body text.
    """

    if not text.startswith("---"):
        return None, text

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text

    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break

    if end_index is None:
        raise FrontmatterParseError("Missing closing frontmatter delimiter '---'")

    yaml_blob = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])

    try:
        if yaml is not None:
            parsed = yaml.safe_load(yaml_blob) if yaml_blob.strip() else {}
        else:
            parsed = _fallback_parse_yaml(yaml_blob) if yaml_blob.strip() else {}
    except Exception as exc:
        raise FrontmatterParseError(str(exc)) from exc

    if parsed is None:
        parsed = {}

    if not isinstance(parsed, dict):
        raise FrontmatterParseError("Frontmatter must parse to a YAML mapping")

    return parsed, body


def parse_frontmatter_file(path: Path):
    """Parse a file and return standardized record with parse state."""

    text = Path(path).read_text(encoding="utf-8")

    try:
        frontmatter, _ = parse_frontmatter_text(text)
        return {
            "filepath": str(path),
            "has_frontmatter": frontmatter is not None,
            "parse_ok": True,
            "frontmatter": frontmatter,
            "error": None,
        }
    except FrontmatterParseError as exc:
        return {
            "filepath": str(path),
            "has_frontmatter": text.startswith("---"),
            "parse_ok": False,
            "frontmatter": None,
            "error": str(exc),
        }
