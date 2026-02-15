"""Render static HTML report for frontmatter insights."""

from html import escape
from pathlib import Path


def _table(headers, rows):
    if not rows:
        return "<p><em>No data</em></p>"

    head = "".join(f"<th>{escape(str(h))}</th>" for h in headers)
    body_rows = []
    for row in rows:
        body_rows.append("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in row) + "</tr>")

    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def render_report_html(out_dir: Path, report_data: dict, chart_paths: dict):
    """Create report.html in out directory."""

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
        chart_sections.append(f"<figure><img src='{escape(rel)}' alt='{escape(name)}'><figcaption>{escape(name)}</figcaption></figure>")

    html = f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<title>Frontmatter Insights</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; color: #111; }}
h1, h2 {{ margin-top: 1.4em; }}
.metrics {{ display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 12px; }}
.metric {{ background: #f4f6fa; border: 1px solid #dce3ef; padding: 10px; border-radius: 6px; }}
figure {{ margin: 1em 0; }}
img {{ max-width: 100%; border: 1px solid #ddd; }}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
th, td {{ border: 1px solid #ddd; text-align: left; padding: 6px; vertical-align: top; }}
th {{ background: #f5f5f5; }}
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
  {''.join(chart_sections)}
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

    report_path = out_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")
    return report_path
