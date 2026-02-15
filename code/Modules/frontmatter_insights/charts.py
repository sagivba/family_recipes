"""Matplotlib chart generation for frontmatter insights report."""

from pathlib import Path

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - dependency fallback
    matplotlib = None
    plt = None


COLOR = "#4C78A8"


def _save_bar_chart(labels, values, title: str, output_path: Path, max_items: int = 25):
    if not labels or not values:
        return None

    labels = list(labels)[:max_items]
    values = list(values)[:max_items]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if plt is None:
        return None

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


def _save_full_barh_chunks(
    labels,
    values,
    title: str,
    output_base: Path,
    chunk_size: int = 50,
):
    if not labels or not values:
        return []

    labels = list(labels)
    values = list(values)
    output_base.parent.mkdir(parents=True, exist_ok=True)

    if plt is None:
        return []

    paths = []
    for idx in range(0, len(labels), chunk_size):
        chunk_labels = labels[idx : idx + chunk_size]
        chunk_values = values[idx : idx + chunk_size]
        chunk_no = idx // chunk_size + 1
        is_multi = len(labels) > chunk_size

        if is_multi:
            output_path = output_base.parent / f"{output_base.stem}_{chunk_no}.png"
            chunk_title = f"{title} (part {chunk_no})"
        else:
            output_path = output_base
            chunk_title = title

        fig_height = max(4.0, 0.28 * len(chunk_labels))
        fig, ax = plt.subplots(figsize=(11, fig_height))
        ax.barh(chunk_labels[::-1], chunk_values[::-1], color=COLOR)
        ax.set_title(chunk_title)
        ax.set_xlabel("Count")
        ax.grid(axis="x", alpha=0.2)
        fig.tight_layout()
        fig.savefig(output_path, dpi=130)
        plt.close(fig)
        paths.append(output_path)

    return paths


def generate_charts(out_dir: Path, profile_data: dict):
    """Generate chart PNGs and return map of chart names to relative paths."""

    out_dir = Path(out_dir)
    charts_dir = out_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    chart_paths = {"charts_available": plt is not None}
    if plt is None:
        (charts_dir / "CHARTS_UNAVAILABLE.txt").write_text(
            "Charts unavailable: matplotlib is not installed.", encoding="utf-8"
        )
        return chart_paths

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
        charts_dir / "keys_presence.png",
    )
    if path:
        chart_paths["keys_presence"] = str(Path("charts") / path.name)

    path = _save_bar_chart(
        [k for k, v in by_empty if v.get("empty_count", 0) > 0],
        [v.get("empty_count", 0) for _, v in by_empty if v.get("empty_count", 0) > 0],
        "Top 25 keys by empty count",
        charts_dir / "keys_empty.png",
    )
    if path:
        chart_paths["keys_empty"] = str(Path("charts") / path.name)

    distributions = profile_data.get("categorical_distributions", {})
    for field in ["category", "origin", "type", "spiciness", "diabetic_friendly", "tags"]:
        dist = distributions.get(field, {})
        if not dist:
            continue
        items = sorted(dist.items(), key=lambda kv: kv[1], reverse=True)
        chart_file = charts_dir / f"dist_{field}.png"
        path = _save_bar_chart(
            [k for k, _ in items],
            [v for _, v in items],
            f"Distribution: {field}",
            chart_file,
        )
        if path:
            chart_paths[f"dist_{field}"] = str(Path("charts") / path.name)

    categorical_tables = profile_data.get("categorical_value_tables", {})
    for field in ["category", "diabetic_friendly", "origin", "source", "spiciness", "type"]:
        details = categorical_tables.get(field, {})
        rows = details.get("rows", [])
        if not rows:
            continue

        full_paths = _save_full_barh_chunks(
            [r.get("value", "") for r in rows],
            [r.get("count", 0) for r in rows],
            f"Distribution: {field}",
            charts_dir / f"dist_all_{field}.png",
            chunk_size=50,
        )
        if full_paths:
            chart_paths[f"dist_all_{field}"] = [str(Path("charts") / p.name) for p in full_paths]

    return chart_paths
