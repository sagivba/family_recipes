"""CLI for frontmatter insights analytics tool."""

from pathlib import Path

import click

from Modules.frontmatter_insights.charts import generate_charts
from Modules.frontmatter_insights.cluster import cluster_keys, cluster_values
from Modules.frontmatter_insights.discover import discover_markdown_files
from Modules.frontmatter_insights.export import (
    write_category_merge_suggestions,
    write_frontmatter_table_csv,
    write_json_report,
)
from Modules.frontmatter_insights.normalize import normalize_record
from Modules.frontmatter_insights.parse_frontmatter import parse_frontmatter_file
from Modules.frontmatter_insights.profile import build_file_rows, profile_frontmatter
from Modules.frontmatter_insights.render_html import render_report_html


def run(root: str = ".", recipes_dir: str = "_recipes", out: str = "out", max_mb: int = 5):
    """Run frontmatter insights generation pipeline."""

    root_path = Path(root)
    out_dir = Path(out)

    files, skipped = discover_markdown_files(root_path, recipes_dir=recipes_dir, max_mb=max_mb)

    parsed = [parse_frontmatter_file(path) for path in files]

    for rec in parsed:
        if rec["parse_ok"] and rec["frontmatter"] is not None:
            rec["frontmatter"] = normalize_record(rec["frontmatter"])

    file_rows, parse_errors = build_file_rows(parsed)

    profile_data = profile_frontmatter(file_rows, skipped_large_files=skipped)
    key_clusters = cluster_keys(file_rows)
    value_clusters = cluster_values(file_rows)

    report_payload = {
        **profile_data,
        "key_clusters": key_clusters,
        "value_clusters": value_clusters,
        "parse_errors": parse_errors,
        "skipped_large_files": skipped,
    }

    json_path = write_json_report(out_dir, report_payload)
    csv_path = write_frontmatter_table_csv(out_dir, file_rows)
    merge_path = write_category_merge_suggestions(out_dir, value_clusters)
    chart_paths = generate_charts(out_dir, profile_data)
    html_path = render_report_html(out_dir, report_payload, chart_paths)

    return {
        "json": json_path,
        "csv": csv_path,
        "html": html_path,
        "merge_suggestions": merge_path,
        "chart_paths": chart_paths,
    }


@click.command(help="Analyze YAML frontmatter in recipe markdown files.")
@click.option("--root", type=click.Path(file_okay=False, path_type=Path), default=Path("."))
@click.option("--recipes-dir", type=str, default="_recipes")
@click.option("--out", type=click.Path(file_okay=False, path_type=Path), default=Path("out"))
@click.option("--max-mb", type=int, default=5)
def main(root: Path, recipes_dir: str, out: Path, max_mb: int):
    results = run(root=str(root), recipes_dir=recipes_dir, out=str(out), max_mb=max_mb)
    click.echo(f"Wrote JSON: {results['json']}")
    click.echo(f"Wrote CSV: {results['csv']}")
    click.echo(f"Wrote HTML: {results['html']}")


if __name__ == "__main__":
    main()
