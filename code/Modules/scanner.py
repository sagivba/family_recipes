"""
File system scanner for recipe files.

This module is responsible for discovering recipe markdown files
within a configured directory.
"""

from pathlib import Path
from typing import List


class ScannerError(Exception):
    """Raised when scanning fails."""
    pass


def scan_recipes(
    recipes_dir: str,
    extension: str = ".md",
) -> List[Path]:
    """
    Scan a directory and return recipe files.

    Responsibilities:
    - Validate input directory
    - Discover files by extension
    - Return a deterministic, sorted list of paths

    Args:
        recipes_dir: Directory to scan
        extension: File extension to include (default: .md)

    Returns:
        A sorted list of Path objects

    Raises:
        ScannerError: If the directory does not exist or is not a directory
    """

    base_path = Path(recipes_dir)

    if not base_path.exists():
        raise ScannerError(f"Recipes directory does not exist: {recipes_dir}")

    if not base_path.is_dir():
        raise ScannerError(f"Recipes path is not a directory: {recipes_dir}")

    files = [
        p for p in base_path.iterdir()
        if p.is_file() and p.suffix.lower() == extension.lower()
    ]

    return sorted(files)
