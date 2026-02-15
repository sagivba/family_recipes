import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.frontmatter_insights.profile import build_file_rows, profile_frontmatter


class TestProfile(unittest.TestCase):
    def test_profile_counts(self):
        parsed = [
            {"filepath": "a.md", "has_frontmatter": True, "parse_ok": True, "frontmatter": {"category": "Soup", "tags": ["quick"]}},
            {"filepath": "b.md", "has_frontmatter": False, "parse_ok": True, "frontmatter": None},
            {"filepath": "c.md", "has_frontmatter": True, "parse_ok": False, "frontmatter": None, "error": "bad yaml"},
        ]
        rows, errors = build_file_rows(parsed)
        report = profile_frontmatter(rows, skipped_large_files=[{"filepath": "big.md"}])

        self.assertEqual(len(errors), 1)
        self.assertEqual(report["totals"]["total_files"], 4)
        self.assertEqual(report["totals"]["parse_error_count"], 1)
        self.assertEqual(report["key_profiles"]["category"]["presence_count"], 1)


if __name__ == "__main__":
    unittest.main()
