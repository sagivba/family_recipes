import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.final_lint import finallint


EXPECTED_KINDS_BY_FILE = {
    "TC02_missing_front_matter.md": {"front_matter_syntax", "front_matter_semantic"},
    "TC03_invalid_yaml.md": {"front_matter_syntax", "front_matter_semantic"},
    "TC04_missing_description_field.md": {"front_matter_semantic"},
    "TC06_wrong_sections_order.md": {"sections"},
    "TC08_extra_header_noise.md": {"sections"},
}


class TestFinalLintOfficialTestcases(unittest.TestCase):
    def setUp(self):
        self.linter = finallint()
        self.roots = [
            PROJECT_ROOT / "_testcases",
            PROJECT_ROOT / "_testcases" / "_all_testcase_files",
        ]

    def test_negative_cases(self):
        for root in self.roots:
            files = sorted(root.glob("TC*.md"))
            self.assertTrue(files, f"No testcase files found in {root}")

            for path in files:
                with self.subTest(path=str(path)):
                    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
                    report = self.linter.lint_text(text, virtual_path=str(path))

                    self.assertFalse(report.ok)
                    self.assertGreater(len(report.issues), 0)

                    actual_kinds = {issue.kind for issue in report.issues}
                    expected_kinds = EXPECTED_KINDS_BY_FILE[path.name]
                    self.assertTrue(
                        actual_kinds.intersection(expected_kinds),
                        f"Expected one of {expected_kinds}, got {actual_kinds}",
                    )

                    codes = [issue.code for issue in report.issues]
                    self.assertTrue(any(code for code in codes))


if __name__ == "__main__":
    unittest.main()
