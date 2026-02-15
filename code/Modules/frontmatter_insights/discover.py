"""File discovery utilities for frontmatter insights."""

from pathlib import Path


ALLOWED_SUFFIXES = {".md", ".mdx"}


def discover_markdown_files(root: Path, recipes_dir: str = "_recipes", max_mb: int = 5):
    """Discover markdown files and skip files larger than *max_mb*.

    Returns:
        tuple[list[Path], list[dict]]: accepted files and skipped file warnings.
    """

    base_dir = Path(root) / recipes_dir
    if not base_dir.exists():
        return [], []

    max_bytes = max_mb * 1024 * 1024
    discovered = []
    skipped = []

    for path in base_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue

        size = path.stat().st_size
        if size > max_bytes:
            skipped.append(
                {
                    "filepath": str(path),
                    "size_bytes": size,
                    "max_bytes": max_bytes,
                    "message": f"File exceeds max size ({max_mb}MB)",
                }
            )
            continue

        discovered.append(path)

    return sorted(discovered), skipped
