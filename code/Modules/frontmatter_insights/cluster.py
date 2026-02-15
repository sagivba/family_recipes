"""Similarity clustering for keys and categorical values."""

from collections import Counter
from difflib import SequenceMatcher

from Modules.frontmatter_insights.normalize import CATEGORICAL_FIELDS


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, str(a), str(b)).ratio()


def _cluster_items(items, threshold):
    clusters = []
    for item in items:
        placed = False
        for cluster in clusters:
            if any(similarity(item, existing) >= threshold for existing in cluster):
                cluster.append(item)
                placed = True
                break
        if not placed:
            clusters.append([item])
    return clusters


def cluster_keys(file_rows, threshold=0.88):
    """Cluster similar keys based on normalized string similarity."""

    key_counter = Counter()
    examples = {}

    for row in file_rows:
        if not row["parse_ok"]:
            continue
        for key in row["frontmatter"].keys():
            key_counter[key] += 1
            examples.setdefault(key, []).append(row["filepath"])

    clusters_raw = _cluster_items(sorted(key_counter.keys()), threshold)
    results = []
    for members in clusters_raw:
        members_sorted = sorted(members, key=lambda k: (-key_counter[k], k))
        results.append(
            {
                "members": members_sorted,
                "counts": {m: key_counter[m] for m in members_sorted},
                "example_filepaths": {
                    m: examples.get(m, [])[:5] for m in members_sorted
                },
            }
        )

    return results


def cluster_values(file_rows, threshold=0.90):
    """Cluster values for selected categorical fields."""

    field_results = {}
    for field in CATEGORICAL_FIELDS:
        value_counter = Counter()
        examples = {}

        for row in file_rows:
            if not row["parse_ok"]:
                continue
            if field not in row["frontmatter"]:
                continue

            value = row["frontmatter"][field]
            values = value if isinstance(value, list) else [value]
            for v in values:
                text = str(v)
                value_counter[text] += 1
                examples.setdefault(text, []).append(row["filepath"])

        clusters_raw = _cluster_items(sorted(value_counter.keys()), threshold)
        clusters = []
        for members in clusters_raw:
            members_sorted = sorted(members, key=lambda x: (-value_counter[x], x))
            clusters.append(
                {
                    "members": members_sorted,
                    "counts": {m: value_counter[m] for m in members_sorted},
                    "example_filepaths": {
                        m: examples.get(m, [])[:5] for m in members_sorted
                    },
                }
            )

        field_results[field] = clusters

    return field_results
