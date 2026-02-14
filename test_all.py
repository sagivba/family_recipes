"""Repository-level unittest entrypoint for finallint tests.

Enables `python -m unittest` from repo root to execute the in-memory
`finallint` test suite without requiring optional dependencies used by
other modules.
"""

from __future__ import annotations

import pathlib
import sys
import unittest


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str):
    root = pathlib.Path(__file__).resolve().parent
    code_dir = root / "code"
    tests_dir = code_dir / "_Tests"

    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

    return loader.discover(
        start_dir=str(tests_dir),
        pattern="test_final_lint.py",
        top_level_dir=str(code_dir),
    )
