"""Render static HTML report for frontmatter insights."""

from html import escape
from pathlib import Path


CATEGORICAL_FIELDS = ["category", "diabetic_friendly", "origin", "source", "spiciness", "type"]


def _table(headers, rows):
    if not rows:
        return "<p><em>No data</em></p>"

    head = "".join(f"<th>{escape(str(h))}</th>" for h in headers)
    body_rows = []
    for row in rows:
        body_rows.append("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in row) + "</tr>")

    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def _render_categorical_sections(report_data: dict, chart_paths: dict):
    categorical_tables = report_data.get("categorical_value_tables", {})

    anchor_links = [
        f"<a href='#field-{escape(field)}'>{escape(field)}</a>" for field in CATEGORICAL_FIELDS
    ]
    nav_html = f"<p class='anchor-links'>{' | '.join(anchor_links)}</p>"

    sections = []
    for field in CATEGORICAL_FIELDS:
        details = categorical_tables.get(field, {})
        rows = details.get("rows", [])

        table_rows = []
        for item in rows:
            examples = ", ".join(item.get("examples", []))
            table_rows.append(
                [
                    item.get("value", ""),
                    item.get("count", 0),
                    f"{item.get('percent', 0):.2f}%",
                    examples,
                ]
            )

        missing_badge = (
            f"<span class='badge'>Missing: {details.get('missing_count', 0)} "
            f"({details.get('missing_pct', 0):.2f}%)</span>"
        )

        chart_key = f"dist_all_{field}"
        chart_rel_paths = chart_paths.get(chart_key, [])
        if isinstance(chart_rel_paths, str):
            chart_rel_paths = [chart_rel_paths]

        chart_html_parts = [
            f"<figure><img src='{escape(rel)}' alt='{escape(chart_key)}'></figure>"
            for rel in chart_rel_paths
        ]

        if not chart_html_parts:
            if not chart_paths.get("charts_available", True):
                chart_html_parts = ["<p><em>Charts unavailable</em></p>"]
            else:
                chart_html_parts = ["<p><em>No chart</em></p>"]

        sections.append(
            f"""
            <section id='field-{escape(field)}'>
              <h3>{escape(field)} {missing_badge}</h3>
              <div class='field-layout'>
                <div class='field-left'>{''.join(chart_html_parts)}</div>
                <div class='field-right'>
                  <h4>All values</h4>
                  {_table(['value', 'count', 'percent', 'examples'], table_rows)}
                </div>
              </div>
            </section>
            """
        )

    return nav_html + "".join(sections)


def render_report_html(out_dir: Path, report_data: dict, chart_paths: dict):
    """Create index.html in out directory (and maintain report.html compatibility)."""

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    totals = report_data.get("totals", {})
    key_clusters = report_data.get("key_clusters", [])
    value_clusters = report_data.get("value_clusters", {})
    parse_errors = report_data.get("parse_errors", [])
    kv_stats = report_data.get("key_value_stats", {})

    key_cluster_rows = []
    for cluster in key_clusters:
        key_cluster_rows.append(
            [
                ", ".join(cluster.get("members", [])),
                str(cluster.get("counts", {})),
                str(cluster.get("example_filepaths", {})),
            ]
        )

    value_cluster_rows = []
    for field, clusters in value_clusters.items():
        for cluster in clusters:
            value_cluster_rows.append(
                [
                    field,
                    ", ".join(cluster.get("members", [])),
                    str(cluster.get("counts", {})),
                ]
            )

    parse_error_rows = [[e.get("filepath", ""), e.get("message", "")] for e in parse_errors]

    top_categories = [
        [item["value"], item["count"]]
        for item in kv_stats.get("category", {}).get("top_values", [])[:20]
    ]
    top_tags = [
        [item["value"], item["count"]]
        for item in kv_stats.get("tags", {}).get("top_values", [])[:20]
    ]

    chart_sections = []
    for name, rel in chart_paths.items():
        if name.startswith("dist_all_") or name == "charts_available":
            continue
        if isinstance(rel, list):
            continue
        chart_sections.append(
            f"<figure><img src='{escape(rel)}' alt='{escape(name)}'><figcaption>{escape(name)}</figcaption></figure>"
        )

    categorical_sections_html = _render_categorical_sections(report_data, chart_paths)
    charts_notice = ""
    if not chart_paths.get("charts_available", True):
        charts_notice = "<p><strong>Charts unavailable</strong></p>"

    html = f"""<!doctype html>
<html lang='he' dir='rtl'>
<head>
<meta charset='utf-8'>
<title>Frontmatter Insights</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; color: #111; direction: rtl; text-align: right; }}
h1, h2 {{ margin-top: 1.4em; }}
.metrics {{ display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 12px; }}
.metric {{ background: #f4f6fa; border: 1px solid #dce3ef; padding: 10px; border-radius: 6px; }}
figure {{ margin: 1em 0; }}
img {{ max-width: 100%; border: 1px solid #ddd; }}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
th, td {{ border: 1px solid #ddd; text-align: right; padding: 6px; vertical-align: top; }}
th {{ background: #f5f5f5; }}
.anchor-links {{ display: flex; flex-wrap: wrap; gap: 10px; }}
.badge {{ background: #eef3ff; border: 1px solid #cbd8ff; border-radius: 4px; padding: 2px 8px; font-size: 0.9em; }}
.field-layout {{ display: flex; flex-direction: row-reverse; gap: 16px; align-items: flex-start; }}
.field-left {{ flex: 1 1 45%; }}
.field-right {{ flex: 1 1 55%; max-height: 640px; overflow: auto; }}
</style>
</head>
<body>
<h1>Frontmatter Insights</h1>
<section>
  <h2>Summary metrics</h2>
  <div class='metrics'>
    <div class='metric'><strong>Total files</strong><br>{totals.get('total_files', 0)}</div>
    <div class='metric'><strong>With frontmatter</strong><br>{totals.get('with_frontmatter', 0)}</div>
    <div class='metric'><strong>Without frontmatter</strong><br>{totals.get('without_frontmatter', 0)}</div>
    <div class='metric'><strong>Parse errors</strong><br>{totals.get('parse_error_count', 0)}</div>
    <div class='metric'><strong>Skipped large files</strong><br>{totals.get('skipped_large_files', 0)}</div>
  </div>
</section>
<section>
  <h2>Charts</h2>
  {charts_notice}
  {''.join(chart_sections)}
</section>
<section>
  <h2>Categorical distributions</h2>
  {categorical_sections_html}
</section>
<section>
  <h2>Key clusters</h2>
  {_table(['members', 'counts', 'example filepaths'], key_cluster_rows)}
</section>
<section>
  <h2>Value clusters</h2>
  {_table(['field', 'members', 'counts'], value_cluster_rows)}
</section>
<section>
  <h2>Parse errors</h2>
  {_table(['filepath', 'message'], parse_error_rows)}
</section>
<section>
  <h2>Top categories</h2>
  {_table(['value', 'count'], top_categories)}
</section>
<section>
  <h2>Top tags</h2>
  {_table(['value', 'count'], top_tags)}
</section>
</body>
</html>"""

    index_path = out_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")

    report_path = out_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")
    return index_path
