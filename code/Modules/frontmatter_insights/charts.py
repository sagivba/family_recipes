"""Matplotlib chart generation for frontmatter insights report."""

import base64
from pathlib import Path

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - dependency fallback
    matplotlib = None
    plt = None


COLOR = "#4C78A8"
# transparent 1x1 PNG
FALLBACK_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wn8wYQAAAAASUVORK5CYII="
)


def _save_bar_chart(labels, values, title: str, output_path: Path, max_items: int = 25):
    if not labels or not values:
        return None

    labels = list(labels)[:max_items]
    values = list(values)[:max_items]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if plt is None:
        output_path.write_bytes(FALLBACK_PNG)
        return output_path

    fig_height = max(4, len(labels) * 0.25)
    fig, ax = plt.subplots(figsize=(11, fig_height))
    ax.barh(labels[::-1], values[::-1], color=COLOR)
    ax.set_title(title)
    ax.set_xlabel("Count")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=130)
    plt.close(fig)
    return output_path


def generate_charts(out_dir: Path, profile_data: dict):
    """Generate chart PNGs and return map of chart names to relative paths."""

    out_dir = Path(out_dir)
    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    chart_paths = {}

    key_profiles = profile_data.get("key_profiles", {})
    by_presence = sorted(
        key_profiles.items(), key=lambda kv: kv[1].get("presence_count", 0), reverse=True
    )
    by_empty = sorted(
        key_profiles.items(), key=lambda kv: kv[1].get("empty_count", 0), reverse=True
    )

    path = _save_bar_chart(
        [k for k, _ in by_presence],
        [v.get("presence_count", 0) for _, v in by_presence],
        "Top 25 keys by presence",
        assets / "keys_presence.png",
    )
    if path:
        chart_paths["keys_presence"] = str(Path("assets") / path.name)

    path = _save_bar_chart(
        [k for k, v in by_empty if v.get("empty_count", 0) > 0],
        [v.get("empty_count", 0) for _, v in by_empty if v.get("empty_count", 0) > 0],
        "Top 25 keys by empty count",
        assets / "keys_empty.png",
    )
    if path:
        chart_paths["keys_empty"] = str(Path("assets") / path.name)

    distributions = profile_data.get("categorical_distributions", {})
    for field in ["category", "origin", "type", "spiciness", "diabetic_friendly", "tags"]:
        dist = distributions.get(field, {})
        if not dist:
            continue
        items = sorted(dist.items(), key=lambda kv: kv[1], reverse=True)
        chart_file = assets / f"dist_{field}.png"
        path = _save_bar_chart(
            [k for k, _ in items],
            [v for _, v in items],
            f"Distribution: {field}",
            chart_file,
        )
        if path:
            chart_paths[f"dist_{field}"] = str(Path("assets") / path.name)

    return chart_paths
