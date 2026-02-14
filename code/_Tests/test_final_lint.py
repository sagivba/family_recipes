import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.final_lint import finallint


VALID_RECIPE = """---
layout: recipe
title: "Test"
category: Main
description: "Something"
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


class TestFinalLint(unittest.TestCase):
    def setUp(self):
        self.linter = finallint()

    def test_front_matter_syntax_missing_space_after_colon(self):
        text = VALID_RECIPE.replace("layout: recipe", "layout:recipe")
        report = self.linter.lint_text(text)

        self.assertFalse(report.ok)
        self.assertTrue(any(i.kind == "front_matter_syntax" for i in report.issues))
        self.assertTrue(any("ERROR" in line for line in report.pretty_lines))

    def test_front_matter_syntax_missing_closing_quote(self):
        text = VALID_RECIPE.replace('title: "Test"', 'title: "Test')
        report = self.linter.lint_text(text)

        self.assertFalse(report.ok)
        messages = [i.message for i in report.issues if i.kind == "front_matter_syntax"]
        self.assertIn('missing " at the end of line', messages)

    def test_semantic_error_missing_required_field(self):
        text = VALID_RECIPE.replace('description: "Something"\n', "")
        report = self.linter.lint_text(text)

        self.assertFalse(report.ok)
        self.assertTrue(any(i.kind == "front_matter_semantic" for i in report.issues))
        self.assertTrue(any("Missing required field 'description'" == i.message for i in report.issues))

    def test_unknown_field_suggests_close_match(self):
        text = VALID_RECIPE.replace(
            'description: "Something"',
            'description: "Something"\ndescriptoin: "typo"',
        )
        report = self.linter.lint_text(text)

        self.assertFalse(report.ok)
        unknown_messages = [
            i.message for i in report.issues if i.kind == "front_matter_semantic"
        ]
        self.assertIn(
            "Unknown field 'descriptoin', did you mean 'description'?",
            unknown_messages,
        )

    def test_sections_invalid_order_or_missing(self):
        text = VALID_RECIPE.replace("## אופן ההכנה\n- b\n", "")
        report = self.linter.lint_text(text)

        self.assertFalse(report.ok)
        self.assertTrue(any(i.kind == "sections" for i in report.issues))

    def test_valid_recipe(self):
        report = self.linter.lint_text(VALID_RECIPE)

        self.assertTrue(report.ok)
        self.assertEqual([], report.issues)

    def test_str_is_deterministic(self):
        text = VALID_RECIPE.replace("layout: recipe", "layout:recipe").replace(
            'title: "Test"',
            'title: "Test',
        )
        report = self.linter.lint_text(text)

        expected = "\n".join(
            [
                "ok=False",
                "front_matter_syntax|E_FM_SPACE|1:8|missing space after ':'",
                "front_matter_syntax|E_FM_QUOTE_CLOSE|2:13|missing \" at the end of line",
                "pretty:",
                "START\t\t---",
                "ERROR 01\tlayout:recipe",
                "ERROR 02\ttitle: \"Test",
                "OK\t\tcategory: Main",
                "OK\t\tdescription: \"Something\"",
                "END\t---",
            ]
        )

        self.assertEqual(expected, str(report))


if __name__ == "__main__":
    unittest.main()
