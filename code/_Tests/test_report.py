import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Allow importing from Modules/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.report import write_file_report, write_index_report
from Modules.fixer import FixResult, FixAction


class TestReport(unittest.TestCase):

    def test_write_file_report(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            fix_result = FixResult(
                path=Path("recipe.md"),
                original="a",
                fixed="b",
                actions=[FixAction("Test fix")],
            )

            report_path = write_file_report(
                output_dir=out,
                fix_result=fix_result,
                diff_html="<div>diff</div>",
            )

            self.assertTrue(report_path.exists())
            content = report_path.read_text(encoding="utf-8")
            self.assertIn("Test fix", content)
            self.assertIn("diff", content)

    def test_write_index_report(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp)

            results = [
                FixResult(
                    path=Path("a.md"),
                    original="a",
                    fixed="b",
                    actions=[FixAction("fix")],
                ),
                FixResult(
                    path=Path("b.md"),
                    original="x",
                    fixed="x",
                    actions=[],
                ),
            ]

            reports = [
                out / "a.html",
                out / "b.html",
            ]

            index_path = write_index_report(out, reports, results)

            self.assertTrue(index_path.exists())
            content = index_path.read_text(encoding="utf-8")
            self.assertIn("a.md", content)
            self.assertIn("b.md", content)
            self.assertIn("Changed", content)
            self.assertIn("Unchanged", content)


if __name__ == "__main__":
    unittest.main()
