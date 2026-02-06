import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Allow importing from Modules/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.cli import run


MINIMAL_CONFIG = {
    "paths": {
        "recipes_dir": "",
        "fixed_dir": "",
        "reports_dir": "",
    },
    "lint": {
        "strict_sections": True,
    },
    "fix": {
        "enabled": True,
        "overwrite": False,
    },
}


VALID_RECIPE = """---
layout: recipe
title: Test
category: Main
description: OK
---
## מצרכים
x
## אופן ההכנה
y
## ערכים תזונתיים (הערכה ל-100 גרם)
z
### ויטמינים ומינרלים בולטים
v
## הערות
n
"""


class TestCLI(unittest.TestCase):

    def test_cli_pipeline_runs(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            drafts = base / "_drafts"
            drafts.mkdir()

            recipe = drafts / "test.md"
            recipe.write_text(VALID_RECIPE, encoding="utf-8")

            fixed = base / "_fixed"
            reports = base / "_reports"

            config = MINIMAL_CONFIG.copy()
            config["paths"] = {
                "recipes_dir": str(drafts),
                "fixed_dir": str(fixed),
                "reports_dir": str(reports),
            }

            run(config)

            self.assertTrue(reports.exists())
            self.assertTrue((reports / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
