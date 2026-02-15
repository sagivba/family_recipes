"""Profiling and aggregation for frontmatter insights."""

from collections import Counter, defaultdict

from Modules.frontmatter_insights.normalize import CATEGORICAL_FIELDS


TYPE_NAMES = {
    str: "str",
    int: "int",
    float: "float",
    bool: "bool",
    list: "list",
    dict: "dict",
    type(None): "none",
}


def _type_name(value):
    for typ, name in TYPE_NAMES.items():
        if isinstance(value, typ):
            return name
    return type(value).__name__


def build_file_rows(parsed_records):
    """Build normalized per-file rows from parser records."""

    rows = []
    parse_errors = []
    for rec in parsed_records:
        row = {
            "filepath": rec["filepath"],
            "has_frontmatter": rec["has_frontmatter"],
            "parse_ok": rec["parse_ok"],
            "frontmatter": rec.get("frontmatter") or {},
        }
        rows.append(row)

        if not rec["parse_ok"]:
            parse_errors.append(
                {"filepath": rec["filepath"], "message": rec.get("error") or "Unknown parse error"}
            )

    return rows, parse_errors


def profile_frontmatter(file_rows, skipped_large_files=None):
    """Compute totals, per-key profiles, and value stats."""

    skipped_large_files = skipped_large_files or []
    total_files = len(file_rows) + len(skipped_large_files)

    with_frontmatter = sum(1 for row in file_rows if row["has_frontmatter"])
    without_frontmatter = len(file_rows) - with_frontmatter
    parse_error_count = sum(1 for row in file_rows if not row["parse_ok"])

    presence = Counter()
    empty_count = Counter()
    type_counts = defaultdict(Counter)
    value_counts = defaultdict(Counter)

    valid_rows = [r for r in file_rows if r["parse_ok"] and r["has_frontmatter"]]

    for row in valid_rows:
        fm = row["frontmatter"]
        for key, value in fm.items():
            presence[key] += 1
            if value in (None, "", [], {}):
                empty_count[key] += 1
            type_counts[key][_type_name(value)] += 1

            if key == "tags":
                if isinstance(value, list):
                    for tag in value:
                        value_counts[key][str(tag)] += 1
                else:
                    value_counts[key][str(value)] += 1
            elif isinstance(value, (str, int, float, bool)) or value is None:
                value_counts[key][str(value)] += 1

    denominator = max(len(file_rows), 1)
    key_profiles = {}
    key_value_stats = {}
    for key in sorted(set(presence.keys()) | set(type_counts.keys())):
        key_profiles[key] = {
            "presence_count": presence[key],
            "presence_pct": round((presence[key] / denominator) * 100, 2),
            "empty_count": empty_count[key],
            "type_counts": dict(type_counts[key]),
        }
        key_value_stats[key] = {
            "unique_count": len(value_counts[key]),
            "top_values": [
                {"value": value, "count": count}
                for value, count in value_counts[key].most_common(20)
            ],
        }

    categorical_distributions = {}
    for field in CATEGORICAL_FIELDS:
        categorical_distributions[field] = dict(value_counts[field].most_common())

    totals = {
        "total_files": total_files,
        "with_frontmatter": with_frontmatter,
        "without_frontmatter": without_frontmatter,
        "parse_error_count": parse_error_count,
        "skipped_large_files": len(skipped_large_files),
    }

    return {
        "totals": totals,
        "key_profiles": key_profiles,
        "key_value_stats": key_value_stats,
        "categorical_distributions": categorical_distributions,
    }
