import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from build_recipes_info import RecipeMetadataExtractor, build_recipes_info


class BuildRecipesInfoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        (self.repo_root / "_recipes").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_recipe(self, name: str, content: str) -> Path:
        path = self.repo_root / "_recipes" / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_extracts_valid_front_matter(self) -> None:
        self._write_recipe("a.md", "---\ntitle: עוגה\nservings: 4\n---\n# Body")

        records = build_recipes_info(self.repo_root)

        self.assertEqual(1, len(records))
        self.assertEqual("עוגה", records[0]["title"])
        self.assertEqual(4, records[0]["servings"])

    def test_ignores_files_without_front_matter(self) -> None:
        self._write_recipe("a.md", "# No front matter")

        records = build_recipes_info(self.repo_root)

        self.assertEqual([], records)

    def test_ignores_invalid_yaml(self) -> None:
        self._write_recipe("a.md", "---\ntitle: [oops\n---\n# Body")

        records = build_recipes_info(self.repo_root)

        self.assertEqual([], records)

    def test_ignores_non_mapping_front_matter(self) -> None:
        self._write_recipe("a.md", "---\n- item1\n- item2\n---\n# Body")

        records = build_recipes_info(self.repo_root)

        self.assertEqual([], records)

    def test_normalizes_missing_fields_across_recipes(self) -> None:
        self._write_recipe("a.md", "---\ntitle: Cake\ncategory: dessert\n---\n")
        self._write_recipe("b.md", "---\ntitle: Soup\n---\n")

        records = build_recipes_info(self.repo_root)

        by_name = {r["filename"]: r for r in records}
        self.assertEqual("dessert", by_name["a.md"]["category"])
        self.assertEqual("", by_name["b.md"]["category"])

        key_sets = {tuple(sorted(r.keys())) for r in records}
        self.assertEqual(1, len(key_sets))

    def test_scans_only_recipes_md_directly_under_recipes(self) -> None:
        self._write_recipe("a.md", "---\ntitle: A\n---\n")
        (self.repo_root / "_recipes" / "notes.txt").write_text("---\ntitle: bad\n---\n", encoding="utf-8")
        nested = self.repo_root / "_recipes" / "nested"
        nested.mkdir()
        (nested / "b.md").write_text("---\ntitle: B\n---\n", encoding="utf-8")

        records = build_recipes_info(self.repo_root)

        self.assertEqual(1, len(records))
        self.assertEqual("a.md", records[0]["filename"])

    def test_filename_and_relative_path(self) -> None:
        self._write_recipe("a.md", "---\ntitle: A\n---\n")

        records = build_recipes_info(self.repo_root)

        self.assertEqual("a.md", records[0]["filename"])
        self.assertEqual("_recipes/a.md", records[0]["relative_path"])

    def test_writes_output_json_with_expected_structure(self) -> None:
        self._write_recipe("a.md", "---\ntitle: A\n---\n")

        build_recipes_info(self.repo_root)

        out_path = self.repo_root / "infographic" / "recipes_info.json"
        self.assertTrue(out_path.exists())
        data = json.loads(out_path.read_text(encoding="utf-8"))
        self.assertIsInstance(data, list)
        self.assertIsInstance(data[0], dict)
        self.assertIn("title", data[0])
        self.assertIn("filename", data[0])
        self.assertIn("relative_path", data[0])

    def test_deterministic_order_by_relative_path(self) -> None:
        self._write_recipe("z.md", "---\ntitle: Z\n---\n")
        self._write_recipe("a.md", "---\ntitle: A\n---\n")

        records = build_recipes_info(self.repo_root)

        self.assertEqual(["a.md", "z.md"], [r["filename"] for r in records])

    def test_extract_front_matter_requires_opening_delimiter_at_top(self) -> None:
        text = "\n---\ntitle: A\n---\n"
        self.assertIsNone(RecipeMetadataExtractor.extract_front_matter(text))


if __name__ == "__main__":
    unittest.main()
