#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import shutil
import sys
import logging

import click

from Modules.scanner import scan_recipes
from Modules.linter import lint_recipe
from Modules.fixer import fix_recipe, FixResult
from Modules.logger import setup_logging
from Modules.report import write_file_report, write_index_report
from Modules.diff_html import generate_diff_html


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _fixed_name(src: Path, fix_dir: Path) -> Path:
    return fix_dir / f"{src.stem}_{_timestamp()}{src.suffix}"


def _require_relative_subdir(opt_value: Path, drafts_dir: Path, opt_name: str) -> Path:
    """
    Enforce that output directories are under drafts_dir.

    Accepts relative paths only. If user passes something like "_drafts/logs",
    and drafts_dir is "_drafts", we strip the leading "_drafts" part and treat
    it as "logs".
    """
    p = Path(opt_value)

    if p.is_absolute():
        raise click.ClickException(
            f"{opt_name} must be a relative path (under {drafts_dir}). Got: {p}"
        )

    # prevent escaping drafts_dir via ".."
    if any(part == ".." for part in p.parts):
        raise click.ClickException(
            f"{opt_name} must not contain '..'. Got: {p}"
        )

    # If user passed "_drafts/logs" while drafts_dir is "_drafts", strip prefix
    if p.parts and p.parts[0] == drafts_dir.name:
        p = Path(*p.parts[1:])

    if str(p).strip() == "" or p == Path("."):
        raise click.ClickException(
            f"{opt_name} must not be empty. Got: {opt_value}"
        )

    return p


@click.command(help="Validate and fix draft recipes before publishing.")
@click.option(
    "--drafts-dir",
    type=click.Path(path_type=Path, exists=True, file_okay=False),
    default=Path("_drafts"),
    show_default=True,
)
@click.option(
    "--fix-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("fix"),
    show_default=True,
    help="Subdirectory under drafts-dir for fixed outputs.",
)
@click.option(
    "--reports-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("reports"),
    show_default=True,
    help="Subdirectory under drafts-dir for HTML reports.",
)
@click.option(
    "--logs-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("logs"),
    show_default=True,
    help="Subdirectory under drafts-dir for log files (non-dry-run only).",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    show_default=True,
)
@click.option("--dry-run", is_flag=True, help="Do not write any files or create any directories.")
@click.option(
    "--fail-on-issues/--no-fail-on-issues",
    default=True,
    show_default=True,
    help="Return exit code 1 if any issues are found.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Print resolved parameters, PWD, and log location.",
)
def main(
    drafts_dir: Path,
    fix_dir: Path,
    reports_dir: Path,
    logs_dir: Path,
    log_level: str,
    dry_run: bool,
    fail_on_issues: bool,
    verbose: bool,
) -> None:

    # Normalize outputs: ALWAYS under drafts_dir
    fix_sub = _require_relative_subdir(fix_dir, drafts_dir, "--fix-dir")
    reports_sub = _require_relative_subdir(reports_dir, drafts_dir, "--reports-dir")
    logs_sub = _require_relative_subdir(logs_dir, drafts_dir, "--logs-dir")

    out_fix_dir = drafts_dir / fix_sub
    out_reports_dir = drafts_dir / reports_sub
    out_logs_dir = drafts_dir / logs_sub

    log_file_path: Path | None = None

    if dry_run:
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
    else:
        setup_logging(
            log_dir=str(out_logs_dir),
            log_name="drafts_checker",
            level=log_level,
        )
        log_files = sorted(out_logs_dir.glob("drafts_checker_*.log"))
        log_file_path = log_files[-1] if log_files else None

    logger = logging.getLogger(__name__)
    if verbose:
        click.echo("=== drafts-checker verbose ===")
        click.echo(f"PWD                : {Path.cwd().resolve()}")
        click.echo(f"drafts_dir         : {drafts_dir.resolve()}")
        click.echo(f"fix_dir            : {out_fix_dir.resolve()}")
        click.echo(f"reports_dir        : {out_reports_dir.resolve()}")
        click.echo(f"logs_dir           : {out_logs_dir.resolve()}")
        click.echo(f"log_level          : {log_level}")
        click.echo(f"dry_run            : {dry_run}")
        click.echo(f"fail_on_issues     : {fail_on_issues}")

        if dry_run:
            click.echo("log_file           : <dry-run: no log file>")
        else:
            click.echo(
                f"log_file           : {log_file_path.resolve()}"
                if log_file_path
                else "log_file           : <not found>"
            )

        click.echo("================================")

    if dry_run:
        click.echo("DRY-RUN: no files will be created.")
    else:
        click.echo(f"Logs written to: {out_logs_dir.resolve()}")

    logger.info("Starting drafts checker")
    logger.info("Drafts dir: %s", drafts_dir)
    logger.info("Fix dir: %s", out_fix_dir)
    logger.info("Reports dir: %s", out_reports_dir)
    logger.info("Logs dir: %s", out_logs_dir)
    logger.info("Dry run: %s", dry_run)

    # --- filesystem prep (non-dry-run only) ---
    if not dry_run:
        out_fix_dir.mkdir(parents=True, exist_ok=True)
        out_reports_dir.mkdir(parents=True, exist_ok=True)

    results: list[FixResult] = []
    report_files: list[Path] = []
    exit_code = 0

    drafts = scan_recipes(str(drafts_dir))

    if not drafts:
        click.echo("No draft recipes found.")
        logger.info("No draft recipes found. Exiting.")
        raise SystemExit(0)

    for draft in drafts:
        logger.info("Processing draft: %s", draft.name)

        lint_result = lint_recipe(draft)

        # --- no issues ---
        if not lint_result.issues:
            logger.info("Draft is valid")

            if not dry_run:
                fixed_path = _fixed_name(draft, out_fix_dir)
                shutil.copy2(draft, fixed_path)
                logger.info("Copied to %s", fixed_path.name)

            original_text = draft.read_text(encoding="utf-8")
            fix_result = FixResult(
                path=draft,
                original=original_text,
                fixed=original_text,
                actions=[],
            )
            results.append(fix_result)
            continue

        # --- issues -> try fixer ---
        logger.warning("Found %d issues", len(lint_result.issues))

        fix_result = fix_recipe(draft)
        results.append(fix_result)

        if fix_result.changed:
            logger.info("Draft was fixed")
            if not dry_run:
                fixed_path = _fixed_name(draft, out_fix_dir)
                fixed_path.write_text(fix_result.fixed, encoding="utf-8")
                logger.info("Written fixed file: %s", fixed_path.name)
        else:
            logger.info("No changes applied by fixer")

        if fail_on_issues:
            exit_code = 1

    # --- reports (non-dry-run only) ---
    if not dry_run:
        for fix_result in results:
            diff_html = generate_diff_html(
                fix_result.original,
                fix_result.fixed,
            )
            report_path = write_file_report(
                output_dir=out_reports_dir,
                fix_result=fix_result,
                diff_html=diff_html,
            )
            report_files.append(report_path)

        write_index_report(out_reports_dir, report_files, results)
        logger.info("Reports written")

    logger.info("Drafts checker finished")

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
