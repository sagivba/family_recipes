# Modules/stage_pipeline.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil
import os
import json
import logging
from typing import Optional, Dict, Any, List


class StagePipeline:
    """
    Manages filesystem stages for a single drafts-checker run.
    Responsible ONLY for file movement, naming, and logging.
    """

    STAGES = {
        "input": "01_input",
        "ai_normalized": "02_ai_normalized",
        "linted": "03_linted",
        "ai_fixed": "04_ai_fixed",
        "ready": "05_ready",
        "rejected": "06_rejected",
    }

    def __init__(
        self,
        base_dir: Path,
        logger: logging.Logger,
        dry_run: bool = False,
        keep_attempts: bool = True,
    ):
        self.base_dir = base_dir
        self.logger = logger
        self.dry_run = dry_run
        self.keep_attempts = keep_attempts

        self.stage_dirs = {
            name: self.base_dir / dirname
            for name, dirname in self.STAGES.items()
        }

        self.reports_dir = self.base_dir / "reports"
        self.logs_dir = self.base_dir / "logs"

    # -------------------------
    # lifecycle
    # -------------------------

    def init_run(self) -> None:
        if self.dry_run:
            self.logger.debug("Dry-run: skipping stage directory creation")
            return

        for d in list(self.stage_dirs.values()) + [self.reports_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.logger.debug("Stage directories initialized")

    # -------------------------
    # public stage transitions
    # -------------------------

    def to_input(self, src: Path) -> Path:
        return self._copy(src, self.stage_dirs["input"])

    def to_ai_normalized(self, src: Path, text: str, attempt: int) -> Path:
        return self._write(src.name, text, self.stage_dirs["ai_normalized"], "ai", attempt)

    def to_linted(self, src: Path) -> Path:
        return self._copy(src, self.stage_dirs["linted"])

    def to_ai_fixed(self, src: Path, text: str, attempt: int) -> Path:
        return self._write(src.name, text, self.stage_dirs["ai_fixed"], "fix", attempt)

    def to_ready(self, src: Path) -> Path:
        return self._copy(src, self.stage_dirs["ready"])

    def to_rejected(self, src: Path, issues: List[str]) -> Path:
        target = self._copy(src, self.stage_dirs["rejected"])
        self._write_metadata(
            target,
            {
                "status": "rejected",
                "issues": issues,
                "timestamp": self._timestamp(),
            },
        )
        return target

    # -------------------------
    # internals
    # -------------------------

    def _copy(self, src: Path, dst_dir: Path) -> Path:
        target = dst_dir / src.name
        self.logger.info("Stage copy: %s -> %s", src, target)

        if self.dry_run:
            return target

        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        return target

    def _write(
        self,
        src_name: str,
        text: str,
        dst_dir: Path,
        suffix: str,
        attempt: Optional[int],
    ) -> Path:
        name = self._make_name(src_name, suffix, attempt)
        target = dst_dir / name
        self.logger.info("Stage write: %s", target)

        if self.dry_run:
            return target

        dst_dir.mkdir(parents=True, exist_ok=True)

        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, target)
        return target

    def _write_metadata(self, target: Path, data: Dict[str, Any]) -> None:
        meta = target.with_suffix(target.suffix + ".meta.json")
        self.logger.info("Writing metadata: %s", meta)

        if self.dry_run:
            return

        meta.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _make_name(src_name: str, suffix: str, attempt: Optional[int]) -> str:
        p = Path(src_name)
        parts = [p.stem]

        if suffix:
            parts.append(suffix)
        if attempt is not None:
            parts.append(f"a{attempt}")

        return "_".join(parts) + p.suffix

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")
