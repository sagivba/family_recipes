import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.frontmatter_insights.discover import discover_markdown_files


class TestDiscover(unittest.TestCase):
    def test_discovers_md_and_mdx_and_skips_large(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            recipes = base / "_recipes"
            recipes.mkdir()
            (recipes / "a.md").write_text("hello", encoding="utf-8")
            (recipes / "b.mdx").write_text("hello", encoding="utf-8")
            (recipes / "c.txt").write_text("ignored", encoding="utf-8")

            large = recipes / "big.md"
            large.write_bytes(b"x" * (2 * 1024 * 1024))

            files, skipped = discover_markdown_files(base, "_recipes", max_mb=1)

            self.assertEqual({p.name for p in files}, {"a.md", "b.mdx"})
            self.assertEqual(len(skipped), 1)
            self.assertIn("big.md", skipped[0]["filepath"])


if __name__ == "__main__":
    unittest.main()
