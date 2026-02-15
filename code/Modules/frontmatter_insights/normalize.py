"""Normalization helpers for frontmatter analysis."""

import re


CATEGORICAL_FIELDS = {
    "category",
    "tags",
    "origin",
    "type",
    "spiciness",
    "diabetic_friendly",
}


def normalize_key(key: str) -> str:
    """Normalize a frontmatter key for analysis."""

    key = str(key).strip().lower()
    key = re.sub(r"[\s\-]+", "_", key)
    key = re.sub(r"_+", "_", key)
    return key.strip("_")


def normalize_string_value(value: str) -> str:
    """Normalize string values by trimming and collapsing spaces."""

    return re.sub(r"\s+", " ", str(value).strip())


def normalize_record(frontmatter: dict | None) -> dict:
    """Normalize keys and selected values for profiling."""

    if not frontmatter:
        return {}

    normalized = {}
    for key, value in frontmatter.items():
        n_key = normalize_key(key)

        if n_key in CATEGORICAL_FIELDS:
            if n_key == "tags":
                normalized[n_key] = normalize_tags(value)
            elif isinstance(value, str):
                normalized[n_key] = normalize_string_value(value)
            else:
                normalized[n_key] = value
        else:
            normalized[n_key] = value

    return normalized


def normalize_tags(value):
    """Normalize tags from string/list into list[str]."""

    if value is None:
        return []

    if isinstance(value, str):
        split_candidates = [v for v in value.split(",")]
        if len(split_candidates) == 1:
            return [normalize_string_value(value)] if normalize_string_value(value) else []
        return [normalize_string_value(v) for v in split_candidates if normalize_string_value(v)]

    if isinstance(value, list):
        items = []
        for item in value:
            n_item = normalize_string_value(item)
            if n_item:
                items.append(n_item)
        return items

    return [normalize_string_value(value)]
