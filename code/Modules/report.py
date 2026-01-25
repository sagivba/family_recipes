"""
HTML report generator.

This module generates per-file HTML reports and a global index
summarizing all processed recipe files.
"""

from pathlib import Path
from typing import List
from html import escape

from Modules.fixer import FixResult


def _safe_filename(name: str) -> str:
    return name.replace(" ", "_")


def write_file_report(
    output_dir: Path,
    fix_result: FixResult,
    diff_html: str,
) -> Path:
    """
    Write an HTML report for a single recipe file.

    Args:
        output_dir: Directory where reports are written
        fix_result: Result of fixing the recipe
        diff_html: HTML diff content

    Returns:
        Path to the generated report file
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    report_name = _safe_filename(fix_result.path.stem) + ".html"
    report_path = output_dir / report_name

    actions_html = ""
    if fix_result.actions:
        actions_html = "<ul>" + "".join(
            f"<li>{escape(a.description)}</li>"
            for a in fix_result.actions
        ) + "</ul>"
    else:
        actions_html = "<p>No fixes applied.</p>"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Recipe Report - {escape(fix_result.path.name)}</title>
</head>
<body>
    <h1>{escape(fix_result.path.name)}</h1>

    <h2>Applied Fixes</h2>
    {actions_html}

    <h2>Diff</h2>
    {diff_html}
</body>
</html>
"""

    report_path.write_text(html, encoding="utf-8")
    return report_path


def write_index_report(
    output_dir: Path,
    reports: List[Path],
    results: List[FixResult],
) -> Path:
    """
    Write a global index HTML report.

    Args:
        output_dir: Directory where reports are written
        reports: Paths to per-file report HTML files
        results: Corresponding FixResult objects

    Returns:
        Path to the index.html file
    """

    rows = []
    for report_path, result in zip(reports, results):
        status = "Changed" if result.changed else "Unchanged"
        rows.append(
            f"<tr>"
            f"<td>{escape(result.path.name)}</td>"
            f"<td>{status}</td>"
            f"<td>{len(result.actions)}</td>"
            f"<td><a href='{report_path.name}'>View</a></td>"
            f"</tr>"
        )

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Recipe Reports Index</title>
</head>
<body>
    <h1>Recipe Reports</h1>

    <table border="1" cellpadding="4" cellspacing="0">
        <tr>
            <th>File</th>
            <th>Status</th>
            <th>Fixes</th>
            <th>Report</th>
        </tr>
        {''.join(rows)}
    </table>
</body>
</html>
"""

    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path
