import csv
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.frontmatter_insights.export import (
    write_category_merge_suggestions,
    write_frontmatter_table_csv,
    write_json_report,
)


class TestExport(unittest.TestCase):
    def test_writes_outputs(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            payload = {"totals": {"total_files": 1}}
            json_path = write_json_report(out, payload)
            self.assertTrue(json_path.exists())
            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["totals"]["total_files"], 1)

            rows = [
                {
                    "filepath": "a.md",
                    "has_frontmatter": True,
                    "parse_ok": True,
                    "frontmatter": {"category": "Soup", "tags": ["x"]},
                }
            ]
            csv_path = write_frontmatter_table_csv(out, rows)
            self.assertTrue(csv_path.exists())

            with csv_path.open(encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("category", content)

            clusters = {"category": [{"members": ["Soup", "Soups"], "counts": {"Soup": 2, "Soups": 1}}]}
            merge_path = write_category_merge_suggestions(out, clusters)
            self.assertTrue(merge_path.exists())
            with merge_path.open(encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
            self.assertEqual(rows[0]["canonical"], "Soup")


if __name__ == "__main__":
    unittest.main()
