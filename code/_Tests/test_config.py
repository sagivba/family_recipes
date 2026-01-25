import sys
import unittest
from pathlib import Path

# Allow importing from Modules/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from Modules.config import Config, ConfigError


class TestConfig(unittest.TestCase):

    def test_load_valid_config(self):
        cfg = {
            "paths": {
                "recipes_dir": "_drafts",
                "fixed_dir": "_fixed",
            },
            "lint": {
                "strict_sections": False,
            },
            "fix": {
                "enabled": True,
                "overwrite": False,
            },
        }

        config = Config(cfg)

        self.assertEqual(config.paths.recipes_dir, "_drafts")
        self.assertFalse(config.lint.strict_sections)
        self.assertTrue(config.fix.enabled)
        self.assertFalse(config.fix.overwrite)

    def test_missing_required_section(self):
        cfg = {
            "paths": {
                "recipes_dir": "_drafts",
                "fixed_dir": "_fixed",
            },
            "fix": {
                "enabled": True,
                "overwrite": False,
            },
        }

        with self.assertRaises(ConfigError):
            Config(cfg)

    def test_missing_required_path_key(self):
        cfg = {
            "paths": {
                "recipes_dir": "_drafts",
            },
            "lint": {
                "strict_sections": True,
            },
            "fix": {
                "enabled": True,
                "overwrite": False,
            },
        }

        with self.assertRaises(ConfigError):
            Config(cfg)

    def test_defaults_applied(self):
        cfg = {
            "paths": {
                "recipes_dir": "_drafts",
                "fixed_dir": "_fixed",
            },
            "lint": {},
            "fix": {},
        }

        config = Config(cfg)

        self.assertTrue(config.logging.enabled)
        self.assertEqual(config.logging.level, "INFO")
        self.assertFalse(config.fix.overwrite)

    def test_invalid_type_raises(self):
        cfg = {
            "paths": {
                "recipes_dir": "_drafts",
                "fixed_dir": "_fixed",
            },
            "lint": {
                "strict_sections": True,
            },
            "fix": {
                "enabled": True,
                "overwrite": "no",
            },
        }

        with self.assertRaises(ConfigError):
            Config(cfg)


if __name__ == "__main__":
    unittest.main()
