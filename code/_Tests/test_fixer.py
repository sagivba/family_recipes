import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Allow importing from Modules/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.fixer import fix_recipe


RECIPE_MISSING_DESC = """---
layout:recipe
title: Test
category: Main
---
## מצרכים
x
"""


class TestFixer(unittest.TestCase):

    def test_fix_adds_description_and_spacing(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "recipe.md"
            path.write_text(RECIPE_MISSING_DESC, encoding="utf-8")

            result = fix_recipe(path)

            self.assertTrue(result.changed)
            self.assertIn("description:", result.fixed)
            self.assertIn("layout: recipe", result.fixed)
            self.assertGreater(len(result.actions), 0)

    def test_no_change_when_already_valid(self):
        content = """---
layout: recipe
title: Test
category: Main
description: OK
---
"""

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.md"
            path.write_text(content, encoding="utf-8")

            result = fix_recipe(path)

            self.assertFalse(result.changed)
            self.assertEqual(len(result.actions), 0)


if __name__ == "__main__":
    unittest.main()
