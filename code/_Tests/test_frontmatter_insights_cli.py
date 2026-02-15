import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.frontmatter_insights.charts import plt
from Modules.frontmatter_insights.cli import run


class TestFrontmatterInsightsCLI(unittest.TestCase):
    def test_run_generates_outputs(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            recipes = root / "_recipes"
            recipes.mkdir()
            (recipes / "a.md").write_text(
                "---\ncategory: Soup\ntags: [quick]\norigin: Italian\nsource: Grandma\nspiciness: mild\ntype: Main\ndiabetic_friendly: yes\n---\nText",
                encoding="utf-8",
            )
            out = root / "out"

            results = run(root=str(root), recipes_dir="_recipes", out=str(out))

            self.assertTrue(results["json"].exists())
            self.assertTrue(results["csv"].exists())
            self.assertTrue(results["html"].exists())
            self.assertTrue(results["merge_suggestions"].exists())
            self.assertTrue((out / "index.html").exists())

            charts_dir = out / "charts"
            self.assertTrue(charts_dir.exists())

            html = (out / "index.html").read_text(encoding="utf-8")
            if plt is None:
                self.assertIn("Charts unavailable", html)
            else:
                self.assertGreaterEqual(len(list(charts_dir.glob("*.png"))), 1)
                self.assertIn("<img", html)
                self.assertIn("charts/", html)


if __name__ == "__main__":
    unittest.main()
