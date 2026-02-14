import importlib.util
import logging
import sys
import unittest
import types
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.final_lint import LintIssue, LintReport
from Modules.stage_pipeline import StagePipeline


DRAFTS_CHECKER_PATH = PROJECT_ROOT / "drafts-checker.py"
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda: None))

spec = importlib.util.spec_from_file_location("drafts_checker", DRAFTS_CHECKER_PATH)
drafts_checker = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = drafts_checker
spec.loader.exec_module(drafts_checker)


class _FakeRewriter:
    def __init__(self):
        self.calls = []

    def rewrite(self, markdown, issues=None, attempt=1):
        self.calls.append(("rewrite", attempt, issues))
        return markdown + f"\n# rewrite-{attempt}"

    def enrich_frontmatter(self, markdown):
        self.calls.append(("enrich_frontmatter", None, None))
        return markdown + "\n# fm"

    def enrich_nutrition(self, markdown):
        self.calls.append(("enrich_nutrition", None, None))
        return "- nutrition"


class TestDraftsCheckerFinalLintIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.base_dir = Path(self.tmp.name)
        self.logger = logging.getLogger("test_drafts_checker")
        self.logger.setLevel(logging.DEBUG)

        self.pipeline = StagePipeline(
            base_dir=self.base_dir,
            logger=self.logger,
            dry_run=False,
        )
        self.pipeline.init_run()

        self.draft = self.base_dir / "draft.md"
        self.draft.write_text(
            "---\nlayout: recipe\ntitle: \"t\"\ncategory: Main\ndescription: \"d\"\n---\n"
            "## מצרכים\n- a\n## אופן ההכנה\n- b\n"
            "## ערכים תזונתיים (הערכה ל-100 גרם)\n- n\n"
            "### ויטמינים ומינרלים בולטים\n- v\n## הערות\n- h\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_run_final_lint_copies_to_linted_stage(self):
        input_path = self.pipeline.to_input(self.draft)

        linted_path, report = drafts_checker.run_final_lint(
            current_path=input_path,
            pipeline=self.pipeline,
        )

        self.assertTrue(linted_path.exists())
        self.assertEqual(linted_path.parent.name, "06_linted")
        self.assertTrue(isinstance(report.ok, bool))

    def test_ai_flow_retries_after_lint_issues_and_then_ready(self):
        rewriter = _FakeRewriter()

        issue = LintIssue(
            kind="sections",
            code="E_SEC_ORDER",
            message="Invalid section order",
            line=None,
            column=None,
        )
        lint_reports = [
            LintReport(ok=False, issues=[issue]),
            LintReport(ok=True, issues=[]),
        ]

        linted_paths = [
            self.base_dir / "06_linted" / "draft_merged_a1.md",
            self.base_dir / "06_linted" / "draft_fix_a2.md",
        ]
        for lp in linted_paths:
            lp.parent.mkdir(parents=True, exist_ok=True)
            lp.write_text("content", encoding="utf-8")

        with patch.object(drafts_checker, "run_final_lint") as run_lint_mock:
            run_lint_mock.side_effect = [
                (linted_paths[0], lint_reports[0]),
                (linted_paths[1], lint_reports[1]),
            ]

            outcome = drafts_checker._process_one_draft(
                draft_path=self.draft,
                pipeline=self.pipeline,
                rewriter=rewriter,
                use_ai=True,
                max_attempts=3,
                fail_on_issues=True,
                dry_run=False,
                logger=self.logger,
            )

        self.assertEqual(run_lint_mock.call_count, 2)
        self.assertEqual(outcome.status, "ready")
        self.assertEqual(outcome.attempts, 2)
        # first rewrite normalize, second rewrite fix with issue strings
        self.assertEqual(rewriter.calls[0][0], "rewrite")
        self.assertIn("sections [E_SEC_ORDER]", rewriter.calls[-1][2][0])

    def test_ai_flow_rejects_when_issues_persist(self):
        rewriter = _FakeRewriter()
        issue = LintIssue(
            kind="front_matter_semantic",
            code="E_FM_REQUIRED_FIELD",
            message="Missing required field 'description'",
            line=None,
            column=None,
        )

        linted_paths = [
            self.base_dir / "06_linted" / "draft_merged_a1.md",
            self.base_dir / "06_linted" / "draft_fix_a2.md",
        ]
        for lp in linted_paths:
            lp.parent.mkdir(parents=True, exist_ok=True)
            lp.write_text("content", encoding="utf-8")

        with patch.object(drafts_checker, "run_final_lint") as run_lint_mock:
            run_lint_mock.side_effect = [
                (linted_paths[0], LintReport(ok=False, issues=[issue])),
                (linted_paths[1], LintReport(ok=False, issues=[issue])),
            ]

            outcome = drafts_checker._process_one_draft(
                draft_path=self.draft,
                pipeline=self.pipeline,
                rewriter=rewriter,
                use_ai=True,
                max_attempts=2,
                fail_on_issues=True,
                dry_run=False,
                logger=self.logger,
            )

        self.assertEqual(run_lint_mock.call_count, 2)
        self.assertEqual(outcome.status, "rejected")
        self.assertEqual(outcome.attempts, 2)
        self.assertTrue(outcome.issues)


if __name__ == "__main__":
    unittest.main()
