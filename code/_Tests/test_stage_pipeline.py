import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import logging
import json

from Modules.stage_pipeline import StagePipeline


class TestStagePipeline(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.base_dir = Path(self.tmp.name)

        # logger מבודד לבדיקה
        self.logger = logging.getLogger("test_stage_pipeline")
        self.logger.setLevel(logging.DEBUG)

        self.pipeline = StagePipeline(
            base_dir=self.base_dir,
            logger=self.logger,
            dry_run=False,
        )

        self.sample_file = self.base_dir / "sample.md"
        self.sample_text = "# Sample\n\ncontent"
        self.sample_file.write_text(self.sample_text, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    # ---------- lifecycle ----------

    def test_init_run_creates_stage_directories(self):
        self.pipeline.init_run()

        for d in self.pipeline.stage_dirs.values():
            self.assertTrue(d.exists(), f"Missing stage dir {d}")

        self.assertTrue(self.pipeline.reports_dir.exists())
        self.assertTrue(self.pipeline.logs_dir.exists())

    # ---------- stages ----------

    def test_to_input_copies_file(self):
        self.pipeline.init_run()
        target = self.pipeline.to_input(self.sample_file)

        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(encoding="utf-8"), self.sample_text)

    def test_to_ai_normalized_writes_new_file(self):
        self.pipeline.init_run()
        out = self.pipeline.to_ai_normalized(
            src=self.sample_file,
            text="AI CONTENT",
            attempt=1,
        )

        self.assertTrue(out.exists())
        self.assertIn("_ai_a1.md", out.name)
        self.assertEqual(out.read_text(encoding="utf-8"), "AI CONTENT")

    def test_to_ready_copies_file(self):
        self.pipeline.init_run()
        inp = self.pipeline.to_input(self.sample_file)
        ready = self.pipeline.to_ready(inp)

        self.assertTrue(ready.exists())
        self.assertEqual(ready.read_text(encoding="utf-8"), self.sample_text)

    def test_to_rejected_creates_meta(self):
        self.pipeline.init_run()
        inp = self.pipeline.to_input(self.sample_file)
        rejected = self.pipeline.to_rejected(
            inp,
            issues=["Missing description", "Bad section order"],
        )

        self.assertTrue(rejected.exists())

        meta = rejected.with_suffix(rejected.suffix + ".meta.json")
        self.assertTrue(meta.exists())

        data = json.loads(meta.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "rejected")
        self.assertEqual(len(data["issues"]), 2)

    # ---------- dry run ----------

    def test_dry_run_creates_nothing(self):
        dry_pipeline = StagePipeline(
            base_dir=self.base_dir,
            logger=self.logger,
            dry_run=True,
        )

        dry_pipeline.init_run()
        out = dry_pipeline.to_input(self.sample_file)

        self.assertFalse(out.exists())
        self.assertEqual(out.parent, self.base_dir / "01_input")

    # ---------- logging ----------

    def test_logging_is_called(self):
        with self.assertLogs("test_stage_pipeline", level="INFO") as cm:
            self.pipeline.init_run()
            self.pipeline.to_input(self.sample_file)

        self.assertTrue(
            any("Stage copy" in msg for msg in cm.output),
            "Expected log entry not found",
        )


if __name__ == "__main__":
    unittest.main()
