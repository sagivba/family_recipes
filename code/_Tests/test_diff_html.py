import sys
import unittest
from pathlib import Path

# Allow importing from Modules/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.diff_html import generate_diff_html


class TestDiffHtml(unittest.TestCase):

    def test_diff_contains_html_structure(self):
        html = generate_diff_html("a", "b")

        self.assertIn("<html>", html)
        self.assertIn("</html>", html)
        self.assertIn("Recipe Diff", html)

    def test_diff_highlights_changes(self):
        original = "line one"
        modified = "line two"

        html = generate_diff_html(original, modified)

        self.assertIn("diff_add", html)
        self.assertIn("diff_sub", html)

    def test_custom_highlight_color(self):
        html = generate_diff_html("a", "b", highlight_color="#123456")

        self.assertIn("#123456", html)


if __name__ == "__main__":
    unittest.main()
