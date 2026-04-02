#!/usr/bin/env python3
"""Build normalized recipe metadata JSON from Markdown front matter."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


class RecipeMetadataExtractor:
    """Extracts and normalizes YAML front matter from recipe markdown files."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.recipes_dir = repo_root / "_recipes"
        self.output_path = repo_root / "infographic" / "recipes_info.json"

    def discover_recipe_files(self) -> list[Path]:
        if not self.recipes_dir.exists():
            return []
        files = [path for path in self.recipes_dir.glob("*.md") if path.is_file()]
        return sorted(files, key=lambda p: p.relative_to(self.repo_root).as_posix())

    @staticmethod
    def extract_front_matter(text: str) -> str | None:
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return None

        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[1:i])
        return None

    @staticmethod
    def _parse_scalar(value: str) -> Any:
        value = value.strip()
        if not value:
            return ""

        if (value.startswith("[") and not value.endswith("]")) or (
            value.endswith("]") and not value.startswith("[")
        ):
            raise ValueError("Malformed inline list")

        if (value.startswith("'") and value.endswith("'")) or (
            value.startswith('"') and value.endswith('"')
        ):
            return value[1:-1]

        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered in {"null", "none", "~"}:
            return None

        if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
            return int(value)

        return value

    @classmethod
    def _fallback_parse_yaml_mapping(cls, yaml_blob: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for raw_line in yaml_blob.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                raise ValueError("Invalid YAML line")
            key, value = line.split(":", 1)
            key = key.strip()
            if not key:
                raise ValueError("Empty YAML key")
            result[key] = cls._parse_scalar(value)
        return result

    @classmethod
    def parse_front_matter(cls, yaml_blob: str) -> dict[str, Any] | None:
        try:
            if yaml is not None:
                parsed = yaml.safe_load(yaml_blob) if yaml_blob.strip() else {}
            else:
                parsed = cls._fallback_parse_yaml_mapping(yaml_blob) if yaml_blob.strip() else {}
        except Exception:
            return None

        if parsed is None:
            return {}
        if not isinstance(parsed, dict):
            return None
        return parsed

    def build_recipe_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []

        for recipe_path in self.discover_recipe_files():
            relative_path = recipe_path.relative_to(self.repo_root).as_posix()
            filename = recipe_path.name

            text = recipe_path.read_text(encoding="utf-8")
            yaml_blob = self.extract_front_matter(text)
            if yaml_blob is None:
                print(f"Warning: skipping {relative_path}: no valid front matter", file=sys.stderr)
                continue

            metadata = self.parse_front_matter(yaml_blob)
            if metadata is None:
                print(f"Warning: skipping {relative_path}: invalid or non-mapping YAML front matter", file=sys.stderr)
                continue

            record = dict(metadata)
            record["filename"] = filename
            record["relative_path"] = relative_path
            records.append(record)

        return self.normalize_records(records)

    @staticmethod
    def normalize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        all_keys = sorted({key for record in records for key in record.keys()})
        normalized: list[dict[str, Any]] = []

        for record in records:
            normalized_record = {key: record.get(key, "") for key in all_keys}
            normalized.append(normalized_record)

        return normalized

    def write_output(self, records: list[dict[str, Any]]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)


def build_recipes_info(repo_root: Path) -> list[dict[str, Any]]:
    extractor = RecipeMetadataExtractor(repo_root=repo_root)
    records = extractor.build_recipe_records()
    extractor.write_output(records)
    return records


def main() -> int:
    build_recipes_info(Path.cwd())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
