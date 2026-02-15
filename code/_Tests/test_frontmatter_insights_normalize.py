import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.frontmatter_insights.normalize import normalize_key, normalize_record, normalize_tags


class TestNormalize(unittest.TestCase):
    def test_normalize_key(self):
        self.assertEqual(normalize_key(" Diabetic-Friendly "), "diabetic_friendly")

    def test_normalize_tags_from_string(self):
        self.assertEqual(normalize_tags("a,  b ,c"), ["a", "b", "c"])

    def test_normalize_record(self):
        record = {"Category ": "  Main  Dish ", "tags": ["  x  ", "y"]}
        n = normalize_record(record)
        self.assertEqual(n["category"], "Main Dish")
        self.assertEqual(n["tags"], ["x", "y"])


if __name__ == "__main__":
    unittest.main()
