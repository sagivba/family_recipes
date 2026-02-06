"""
HTML diff generator.

This module generates an HTML representation of differences
between two text versions, highlighting changes.
"""

import difflib
from typing import List


DEFAULT_HIGHLIGHT_COLOR = "#fff59d"


def generate_diff_html(
    original: str,
    modified: str,
    highlight_color: str = DEFAULT_HIGHLIGHT_COLOR,
) -> str:
    """
    Generate an HTML diff between two text blocks.

    Args:
        original: Original text content
        modified: Modified text content
        highlight_color: Background color for highlighted changes

    Returns:
        A complete HTML document as a string
    """

    original_lines: List[str] = original.splitlines()
    modified_lines: List[str] = modified.splitlines()

    differ = difflib.HtmlDiff(
        wrapcolumn=120,
        tabsize=4
    )

    diff_table = differ.make_table(
        original_lines,
        modified_lines,
        fromdesc="Original",
        todesc="Fixed",
        context=False,
        numlines=0,
    )

    style = f"""
    <style>
        body {{
            font-family: monospace;
            background-color: #ffffff;
        }}
        table.diff {{
            width: 100%;
            border-collapse: collapse;
        }}
        .diff_header {{
            background-color: #f0f0f0;
        }}
        td {{
            padding: 2px 4px;
            vertical-align: top;
            white-space: pre-wrap;
        }}
        .diff_add {{
            background-color: {highlight_color};
        }}
        .diff_chg {{
            background-color: {highlight_color};
        }}
        .diff_sub {{
            background-color: {highlight_color};
        }}
    </style>
    """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Recipe Diff</title>
        {style}
    </head>
    <body>
        <h2>Recipe Diff</h2>
        {diff_table}
    </body>
    </html>
    """

    return html
