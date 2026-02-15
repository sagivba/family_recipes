import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.frontmatter_insights.cli import run


class TestFrontmatterInsightsCLI(unittest.TestCase):
    def test_run_generates_outputs(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            recipes = root / "_recipes"
            recipes.mkdir()
            (recipes / "a.md").write_text("---\ncategory: Soup\ntags: [quick]\n---\nText", encoding="utf-8")
            out = root / "out"

            results = run(root=str(root), recipes_dir="_recipes", out=str(out))

            self.assertTrue(results["json"].exists())
            self.assertTrue(results["csv"].exists())
            self.assertTrue(results["html"].exists())
            self.assertTrue(results["merge_suggestions"].exists())


if __name__ == "__main__":
    unittest.main()
