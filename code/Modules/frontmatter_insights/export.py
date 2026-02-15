"""Export utilities for frontmatter insights outputs."""

import csv
import json
from pathlib import Path


def write_json_report(out_dir: Path, payload: dict, filename: str = "frontmatter_insights.json") -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_frontmatter_table_csv(out_dir: Path, file_rows: list[dict], filename: str = "frontmatter_table.csv") -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename

    key_union = sorted(
        {
            key
            for row in file_rows
            for key in (row.get("frontmatter") or {}).keys()
        }
    )
    fieldnames = ["filepath", "has_frontmatter", "parse_ok"] + key_union

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in file_rows:
            output = {
                "filepath": row["filepath"],
                "has_frontmatter": row["has_frontmatter"],
                "parse_ok": row["parse_ok"],
            }
            fm = row.get("frontmatter") or {}
            for key in key_union:
                value = fm.get(key)
                if isinstance(value, (dict, list)):
                    output[key] = json.dumps(value, ensure_ascii=False)
                elif value is None:
                    output[key] = ""
                else:
                    output[key] = str(value)

            writer.writerow(output)

    return path


def write_category_merge_suggestions(out_dir: Path, value_clusters: dict, filename: str = "category_merge_suggestions.csv") -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename

    with path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["field", "canonical", "members", "total_count"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for field, clusters in value_clusters.items():
            for cluster in clusters:
                members = cluster.get("members", [])
                counts = cluster.get("counts", {})
                if not members:
                    continue
                canonical = max(members, key=lambda m: counts.get(m, 0))
                writer.writerow(
                    {
                        "field": field,
                        "canonical": canonical,
                        "members": " | ".join(members),
                        "total_count": sum(counts.values()),
                    }
                )

    return path
