import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.frontmatter_insights.parse_frontmatter import parse_frontmatter_text, parse_frontmatter_file


class TestParseFrontmatter(unittest.TestCase):
    def test_parse_valid_frontmatter(self):
        text = "---\ntitle: Soup\ntags:\n  - vegan\n---\nBody"
        data, body = parse_frontmatter_text(text)
        self.assertEqual(data["title"], "Soup")
        self.assertEqual(data["tags"], ["vegan"])
        self.assertEqual(body, "Body")

    def test_no_frontmatter(self):
        data, body = parse_frontmatter_text("# Heading")
        self.assertIsNone(data)
        self.assertEqual(body, "# Heading")

    def test_parse_error_recorded(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.md"
            path.write_text("---\ntitle [oops\n---", encoding="utf-8")
            rec = parse_frontmatter_file(path)
            self.assertFalse(rec["parse_ok"])
            self.assertTrue(rec["has_frontmatter"])
            self.assertIsNotNone(rec["error"])


if __name__ == "__main__":
    unittest.main()
