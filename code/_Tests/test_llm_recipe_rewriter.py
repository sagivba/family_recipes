import unittest
from unittest.mock import MagicMock
import logging
import sys
from pathlib import Path

# Allow importing from Modules/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.llm_recipe_rewriter import LLMRecipeRewriter


class TestLLMRecipeRewriter(unittest.TestCase):

    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_logger = logging.getLogger("test")
        self.rewriter = LLMRecipeRewriter(
            client=self.mock_client,
            model="gpt-test",
            logger=self.mock_logger,
        )

    def _mock_llm_response(self, text):
        response = MagicMock()
        response.choices = [
            MagicMock(
                message=MagicMock(content=text)
            )
        ]
        self.mock_client.chat.completions.create.return_value = response

    def test_strip_markdown_fence_basic(self):
        fenced = """```markdown
---
layout: recipe
title: Test
---
content
```"""

        self._mock_llm_response(fenced)
        out = self.rewriter.rewrite("input")

        self.assertFalse(out.strip().startswith("```"))
        self.assertFalse(out.strip().endswith("```"))
        self.assertIn("layout: recipe", out)

    def test_no_fence_no_change(self):
        plain = """---
layout: recipe
title: Test
---
content"""

        self._mock_llm_response(plain)
        out = self.rewriter.rewrite("input")

        self.assertEqual(out, plain)

    def test_empty_content(self):
        self._mock_llm_response("")
        out = self.rewriter.rewrite("input")
        self.assertEqual(out, "")

    def test_malformed_fence_returns_empty(self):
        bad = """```
only one line
```"""
        self._mock_llm_response(bad)
        out = self.rewriter.rewrite("input")
        self.assertEqual(out, "only one line")

    def test_logger_called_on_fence(self):
        with self.assertLogs(self.mock_logger, level="INFO") as cm:
            fenced = """```
test
```"""
            self._mock_llm_response(fenced)
            self.rewriter.rewrite("input")

        self.assertTrue(
            any("code fence" in msg for msg in cm.output)
        )


if __name__ == "__main__":
    unittest.main()
