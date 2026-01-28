import sys
from pathlib import Path

# Ensure "code/" is on sys.path (PyCharm / pytest compatibility)
CODE_DIR = Path(__file__).resolve().parents[1]
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import unittest
from unittest.mock import MagicMock

from Modules.llm_recipe_rewriter import LLMRecipeRewriter


class TestLLMRecipeRewriter(unittest.TestCase):

    def setUp(self):
        self.fake_client = MagicMock()

        self.rewriter = LLMRecipeRewriter(
            client=self.fake_client,
            model="fake-model",
            logger=None,
        )

        self.original_md = """---
title: Test
---

## מצרכים
- item
"""

    # -------------------------
    # helpers
    # -------------------------

    def _mock_llm_response(self, content: str):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=content
                )
            )
        ]
        return mock_response

    # -------------------------
    # tests
    # -------------------------

    def test_rewrite_normalize(self):
        normalized_md = """---
title: Test
description: Normalized
---

## מצרכים
- item
"""

        self.fake_client.chat.completions.create.return_value = \
            self._mock_llm_response(normalized_md)

        result = self.rewriter.rewrite(self.original_md)

        self.assertEqual(result, normalized_md)
        self.fake_client.chat.completions.create.assert_called_once()

        # Verify messages sent
        kwargs = self.fake_client.chat.completions.create.call_args.kwargs
        self.assertIn("messages", kwargs)
        self.assertIn("Input:", kwargs["messages"][0]["content"])

    def test_rewrite_fix_with_issues(self):
        fixed_md = """---
title: Test
description: Fixed
---

## מצרכים
- item
"""

        self.fake_client.chat.completions.create.return_value = \
            self._mock_llm_response(fixed_md)

        issues = [
            "Missing description",
            "Invalid front matter",
        ]

        result = self.rewriter.rewrite(
            self.original_md,
            issues=issues,
            attempt=2,
        )

        self.assertEqual(result, fixed_md)
        self.fake_client.chat.completions.create.assert_called_once()

        prompt = self.fake_client.chat.completions.create.call_args.kwargs[
            "messages"
        ][0]["content"]

        self.assertIn("Missing description", prompt)
        self.assertIn("Invalid front matter", prompt)
        self.assertIn("Fix ONLY the listed issues", prompt)

    def test_logger_is_optional(self):
        rewriter = LLMRecipeRewriter(
            client=self.fake_client,
            model="fake-model",
            logger=None,
        )

        self.fake_client.chat.completions.create.return_value = \
            self._mock_llm_response(self.original_md)

        # Should not raise
        result = rewriter.rewrite(self.original_md)
        self.assertEqual(result, self.original_md)


if __name__ == "__main__":
    unittest.main()
