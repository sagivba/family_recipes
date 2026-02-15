import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.frontmatter_insights.charts import generate_charts, plt
from Modules.frontmatter_insights.render_html import render_report_html


class TestRenderHTML(unittest.TestCase):
    def test_report_and_png_created(self):
        if plt is None:
            self.skipTest("matplotlib not installed")

        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            profile_data = {
                "key_profiles": {
                    "category": {"presence_count": 2, "empty_count": 0},
                    "tags": {"presence_count": 2, "empty_count": 0},
                },
                "categorical_distributions": {
                    "category": {"Soup": 2},
                    "tags": {"quick": 2},
                },
            }
            charts = generate_charts(out, profile_data)
            self.assertTrue(charts)

            report_data = {
                "totals": {
                    "total_files": 2,
                    "with_frontmatter": 2,
                    "without_frontmatter": 0,
                    "parse_error_count": 0,
                    "skipped_large_files": 0,
                },
                "key_clusters": [],
                "value_clusters": {},
                "parse_errors": [],
                "key_value_stats": {
                    "category": {"top_values": [{"value": "Soup", "count": 2}]},
                    "tags": {"top_values": [{"value": "quick", "count": 2}]},
                },
                "categorical_value_tables": {
                    "category": {
                        "rows": [{"value": "Soup", "count": 2, "percent": 100, "examples": ["Soup"]}],
                        "missing_count": 0,
                        "missing_pct": 0,
                    }
                },
            }
            html_path = render_report_html(out, report_data, charts)

            self.assertTrue(html_path.exists())
            pngs = list((out / "charts").glob("*.png"))
            self.assertGreaterEqual(len(pngs), 1)


if __name__ == "__main__":
    unittest.main()
