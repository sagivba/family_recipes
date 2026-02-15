#!/usr/bin/env python3
from __future__ import annotations

import sys
import shutil
from pathlib import Path
from datetime import datetime

# Allow running as: python code/frontmatter-insights.py
THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent
CODE_DIR = REPO_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))


def _update_latest(out_base: Path, run_dir: Path) -> None:
    """
    Update <out_base>/latest to point to <run_dir>.
    Prefer symlink; fallback to copy.
    """
    latest = out_base / "latest"

    # Remove existing latest (symlink or directory)
    if latest.exists() or latest.is_symlink():
        if latest.is_dir() and not latest.is_symlink():
            shutil.rmtree(latest)
        else:
            latest.unlink(missing_ok=True)

    # Try relative symlink: latest -> runs/<timestamp>
    try:
        rel_target = run_dir.relative_to(out_base)
        latest.symlink_to(rel_target, target_is_directory=True)
        return
    except Exception:
        # Fallback: copy run_dir contents into latest/
        latest.mkdir(parents=True, exist_ok=True)
        shutil.copytree(run_dir, latest, dirs_exist_ok=True)


def main(argv: list[str]) -> int:
    """
    Wrapper runner for frontmatter_insights.
    Defaults:
      root: repo root
      recipes-dir: _recipes
      out-base: _reports/frontmatter_insights
    """
    root_dir = REPO_ROOT
    recipes_dir = "_recipes"
    out_base = REPO_ROOT / "_reports" / "frontmatter_insights"
    max_mb = 5

    # Minimal args parsing (intentionally simple, like drafts-checker.py)
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--root" and i + 1 < len(argv):
            root_dir = Path(argv[i + 1]).expanduser().resolve()
            i += 2
        elif a == "--recipes-dir" and i + 1 < len(argv):
            recipes_dir = argv[i + 1]
            i += 2
        elif a == "--out-base" and i + 1 < len(argv):
            out_base = Path(argv[i + 1]).expanduser().resolve()
            i += 2
        elif a == "--max-mb" and i + 1 < len(argv):
            max_mb = int(argv[i + 1])
            i += 2
        elif a in ("-h", "--help"):
            print(
                "Usage: python code/frontmatter-insights.py [OPTIONS]\n"
                "\n"
                "Options:\n"
                "  --root PATH         Repo root (default: repo root)\n"
                "  --recipes-dir NAME  Recipes dir name under root (default: _recipes)\n"
                "  --out-base PATH     Output base dir (default: ./_reports/frontmatter_insights)\n"
                "  --max-mb N          Skip files larger than N MB (default: 5)\n"
            )
            return 0
        else:
            print(f"Unknown arg: {a}\nUse --help.", file=sys.stderr)
            return 2

    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir = out_base / "runs" / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    # Click command is `main` in Modules.frontmatter_insights.cli
    from Modules.frontmatter_insights.cli import main as click_main  # type: ignore

    click_args = [
        "--root",
        str(root_dir),
        "--recipes-dir",
        recipes_dir,
        "--out",
        str(run_dir),
        "--max-mb",
        str(max_mb),
    ]

    try:
        click_main.main(args=click_args, standalone_mode=False)
    except SystemExit as e:
        code = int(e.code or 0)
        if code != 0:
            return code

    _update_latest(out_base, run_dir)

    latest = out_base / "latest"
    print("Report written to:")
    print(f"  {run_dir}")
    print("Latest:")
    print(f"  {latest}")
    print("Open:")
    print(f"  {latest / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

