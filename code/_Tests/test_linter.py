import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Allow importing from Modules/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.linter import lint_recipe


VALID_RECIPE = """---
layout: recipe
title: Test
category: Main
description: Something
---
## מצרכים
- a
## אופן ההכנה
- b
## ערכים תזונתיים (הערכה ל-100 גרם)
x
### ויטמינים ומינרלים בולטים
y
## הערות
z
"""


class TestLinter(unittest.TestCase):

    def test_valid_recipe(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.md"
            path.write_text(VALID_RECIPE, encoding="utf-8")

            result = lint_recipe(path)

            self.assertTrue(result.is_valid)
            self.assertEqual(len(result.issues), 0)

    def test_missing_front_matter(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.md"
            path.write_text("no front matter", encoding="utf-8")

            result = lint_recipe(path)

            self.assertFalse(result.is_valid)

    def test_missing_required_field(self):
        with TemporaryDirectory() as tmp:
            content = VALID_RECIPE.replace("description: Something\n", "")
            path = Path(tmp) / "bad.md"
            path.write_text(content, encoding="utf-8")

            result = lint_recipe(path)

            self.assertFalse(result.is_valid)
            messages = [i.message for i in result.issues]
            self.assertIn(
                "Missing required front matter field: 'description'",
                messages,
            )

    def test_invalid_section_order(self):
        with TemporaryDirectory() as tmp:
            content = VALID_RECIPE.replace("## מצרכים", "## הערות")
            path = Path(tmp) / "bad.md"
            path.write_text(content, encoding="utf-8")

            result = lint_recipe(path)

            self.assertFalse(result.is_valid)


if __name__ == "__main__":
    unittest.main()
