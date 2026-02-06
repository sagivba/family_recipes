import sys
import unittest
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

# Allow importing from Modules/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.logger import setup_logging, LoggerError


class TestLogger(unittest.TestCase):

    def _cleanup_logging(self):
        logging.shutdown()
        root = logging.getLogger()
        for h in list(root.handlers):
            try:
                h.close()
            except Exception:
                pass
            root.removeHandler(h)

    def _get_log_files(self, tmp_dir: str):
        return list(Path(tmp_dir).glob("application_*.log"))

    def test_creates_log_directory_and_file(self):
        tmp = TemporaryDirectory()
        try:
            setup_logging(log_dir=tmp.name, log_name="application", level="INFO")
            log_files = self._get_log_files(tmp.name)
            self.assertEqual(len(log_files), 1)
        finally:
            self._cleanup_logging()
            tmp.cleanup()

    def test_invalid_log_level_raises(self):
        tmp = TemporaryDirectory()
        try:
            with self.assertRaises(LoggerError):
                setup_logging(log_dir=tmp.name, level="NOT_A_LEVEL")
        finally:
            self._cleanup_logging()
            tmp.cleanup()

    def test_logging_writes_to_file(self):
        tmp = TemporaryDirectory()
        try:
            setup_logging(log_dir=tmp.name, log_name="application", level="INFO")
            logger = logging.getLogger("test")
            logger.info("test message")

            log_files = self._get_log_files(tmp.name)
            self.assertEqual(len(log_files), 1)

            content = log_files[0].read_text(encoding="utf-8")
            self.assertIn("test message", content)
        finally:
            self._cleanup_logging()
            tmp.cleanup()

    def test_log_rotation_enabled(self):
        tmp = TemporaryDirectory()
        try:
            setup_logging(
                log_dir=tmp.name,
                log_name="application",
                level="INFO",
                rotate=True,
                max_size_mb=1,
                backups=2,
            )
            logger = logging.getLogger("rotate_test")
            logger.info("rotation test")

            log_files = self._get_log_files(tmp.name)
            self.assertEqual(len(log_files), 1)
        finally:
            self._cleanup_logging()
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
