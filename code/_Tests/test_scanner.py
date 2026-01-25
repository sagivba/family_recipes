import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Allow importing from Modules/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.scanner import scan_recipes, ScannerError


class TestScanner(unittest.TestCase):

    def test_scan_finds_markdown_files(self):
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "a.md").write_text("test", encoding="utf-8")
            (base / "b.md").write_text("test", encoding="utf-8")
            (base / "ignore.txt").write_text("test", encoding="utf-8")

            files = scan_recipes(tmp)

            self.assertEqual(len(files), 2)
            self.assertEqual(files[0].name, "a.md")
            self.assertEqual(files[1].name, "b.md")

    def test_scan_empty_directory(self):
        with TemporaryDirectory() as tmp:
            files = scan_recipes(tmp)
            self.assertEqual(files, [])

    def test_nonexistent_directory_raises(self):
        with self.assertRaises(ScannerError):
            scan_recipes("_does_not_exist_")

    def test_path_is_file_raises(self):
        with TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "file.md"
            file_path.write_text("test", encoding="utf-8")

            with self.assertRaises(ScannerError):
                scan_recipes(str(file_path))


if __name__ == "__main__":
    unittest.main()
