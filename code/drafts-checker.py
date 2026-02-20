#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
import os
import sys
import logging
import click
import re

from Modules.scanner import scan_recipes
from Modules.fixer import fix_recipe, FixResult
from Modules.logger import setup_logging
from Modules.report import write_file_report, write_index_report
from Modules.diff_html import generate_diff_html
from Modules.stage_pipeline import StagePipeline
from Modules.llm_recipe_rewriter import LLMRecipeRewriter
from Modules.final_lint import finallint, LintIssue as FinalLintIssue, LintReport
from dotenv import load_dotenv
load_dotenv()


HELP_MSG=  """
    Drafts Checker – Stage-Based Preparation Tool for Publishing Recipes
    
    This tool prepares recipe draft files for publication using a structured, multi-stage pipeline.
    It is designed to run locally and can optionally use an LLM (Large Language Model) to normalize
    and fix drafts before publication.
    
    WHAT THE TOOL DOES
    - Scans a drafts directory for Markdown recipe files
    - Copies each file through numbered processing stages (no in-place edits)
    - Runs validation and linting checks
    - Optionally rewrites or fixes drafts using an LLM with bounded retries
    - Produces HTML reports, diffs, and logs
    - Returns meaningful exit codes for CI or automation
    
    PROCESSING STAGES
    Each file is copied through numbered folders representing its lifecycle:
    01_input          - Original snapshot of the draft
    02_ai_normalized  - Initial LLM normalization (optional)
    03_linted         - Validation and linting checks
    04_ai_fixed       - LLM or deterministic fixes (if needed)
    05_ready          - Files ready for publication
    06_rejected       - Files that failed validation after all attempts
    
    LLM / OPENAI USAGE (OPTIONAL)
    To enable LLM-based processing, run the tool with the --use-ai flag.
    
    The tool requires an API key provided via an environment variable.
    
    REQUIRED ENVIRONMENT VARIABLE
    OPENAI_API_KEY
    Your API key for the OpenAI-compatible API endpoint.
    
    HOW TO SET THE VARIABLE
    
    Windows (PowerShell):
    setx OPENAI_API_KEY "your_api_key_here"
    
    Linux / macOS:
    export OPENAI_API_KEY="your_api_key_here"
    
    You can generate and manage your API key at:
    https://platform.openai.com/account/api-keys
    
    OPTIONAL ENVIRONMENT VARIABLE
    OPENAI_BASE_URL
    Use this if you work with a proxy or an OpenAI-compatible endpoint.
    
    IMPORTANT NOTES
    - Original draft files are never modified
    - All outputs are written to stage directories
    - LLM usage is optional; deterministic mode is supported
    - Exit code 0 indicates success
    - Non-zero exit codes indicate validation failures
    
    This tool is intended to serve as a staging and quality gate before
    promoting drafts to published recipes.
    """

@dataclass
class ProcessOutcome:
    original_path: Path
    final_path: Path
    status: str  # "ready" | "rejected"
    attempts: int
    issues: List[FinalLintIssue]
    fix_result: FixResult


def _safe_resolve(p: Optional[Path]) -> str:
    if not p:
        return "<not available>"
    try:
        return str(p.resolve())
    except Exception:
        return str(p)


def _build_openai_client() -> object:
    """
    Create an OpenAI client using environment variables.

    Expected:
      - OPENAI_API_KEY
    Optional:
      - OPENAI_BASE_URL (for proxies / compatible endpoints)
    """
    try:
        # OpenAI Python SDK v1 style
        from openai import OpenAI  # type: ignore
    except Exception as e:
        raise click.ClickException(
            "OpenAI SDK is not installed. Install it with: pip install openai"
        ) from e

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise click.ClickException(
            "OPENAI_API_KEY is not set. Set it in your environment before using --use-ai."
        )

    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)

    return OpenAI(api_key=api_key)


def _collect_issue_strings(issues: List[FinalLintIssue]) -> List[str]:
    formatted: List[str] = []
    for issue in issues:
        location = (
            f"{issue.line if issue.line is not None else '-'}:"
            f"{issue.column if issue.column is not None else '-'}"
        )
        formatted.append(
            f"{issue.kind} [{issue.code or '-'}] at {location} - {issue.message}"
        )
    return formatted


def run_final_lint(
    *,
    current_path: Path,
    pipeline: StagePipeline,
) -> tuple[Path, LintReport]:
    text = current_path.read_text(encoding="utf-8", errors="replace")
    report = finallint().lint_text(text, virtual_path=str(current_path))
    linted_path = pipeline.to_linted(current_path)
    return linted_path, report


def _write_reports(
    *,
    output_dir: Path,
    outcomes: List[ProcessOutcome],
    dry_run: bool,
    logger: logging.Logger,
) -> None:
    if dry_run:
        return

    report_files: List[Path] = []
    results: List[FixResult] = [o.fix_result for o in outcomes]

    for o in outcomes:
        diff_html = generate_diff_html(o.fix_result.original, o.fix_result.fixed)
        report_path = write_file_report(
            output_dir=output_dir,
            fix_result=o.fix_result,
            diff_html=diff_html,
        )
        report_files.append(report_path)

    write_index_report(output_dir, report_files, results)
    logger.info("Reports written")


def _process_one_draft(
    *,
    draft_path: Path,
    pipeline: StagePipeline,
    rewriter: Optional[LLMRecipeRewriter],
    use_ai: bool,
    max_attempts: int,
    fail_on_issues: bool,
    dry_run: bool,
    logger: logging.Logger,
) -> ProcessOutcome:
    """
    Stage flow per file:

    - Copy original to 01_input
    - If use_ai:
        - attempt 1: AI normalize -> 02_ai_normalized
        - enrich frontmatter -> 03_ai_enriched_frontmatter
        - enrich nutrition (partial) -> 04_ai_enriched_nutrition
        - merge nutrition into full doc -> 05_ai_merged
        - lint
        - if issues: attempt 2..N: AI fix -> 07_ai_fixed, lint again
    - Else:
        - lint original
        - if issues: run deterministic fixer once

    - If lint passes: copy final into 08_ready
      Else: copy last into 09_rejected + metadata
    """

    # Snapshot input
    input_path = pipeline.to_input(draft_path)

    original_text = draft_path.read_text(encoding="utf-8", errors="replace")
    current_text = original_text
    current_path = input_path

    attempts = 0
    last_issues: List[FinalLintIssue] = []

    if use_ai:
        if not rewriter:
            raise RuntimeError("Internal error: use_ai=True but rewriter is None")

        # === Attempt 1: normalize ===
        attempts = 1
        logger.info("AI normalize attempt=%d for %s", attempts, draft_path.name)

        current_text = rewriter.rewrite(current_text, issues=None, attempt=attempts)
        current_path = pipeline.to_ai_normalized(
            input_path, current_text, attempt=attempts
        )

        # === Stage 03: enrich front matter (FULL) ===
        logger.info("AI front-matter enrichment for %s", draft_path.name)

        current_text = enrich_frontmatter_with_ai(
            rewriter=rewriter,
            markdown=current_text,
            logger=logger,
        )
        current_path = pipeline.to_enriched_frontmatter(
            current_path, current_text, attempt=attempts
        )

        # === Stage 04: enrich nutrition (PARTIAL) ===
        logger.info("AI nutrition enrichment for %s", draft_path.name)

        nutrition_block = enrich_nutrition_with_ai(
            rewriter=rewriter,
            markdown=current_text,
            logger=logger,
        )

        nutrition_path = pipeline.to_enriched_nutrition(
            current_path, nutrition_block, attempt=attempts
        )

        # === Stage 05: merge nutrition into FULL document ===
        logger.info("Merging nutrition into recipe for %s", draft_path.name)

        current_text = merge_nutrition_sections(
            original=current_text,
            nutrition_block=nutrition_block,
        )

        current_path = pipeline.to_merged(
            current_path, current_text, attempt=attempts
        )

        # === Lint AFTER merge only ===
        current_path, lint_report = run_final_lint(
            current_path=current_path,
            pipeline=pipeline,
        )
        last_issues = lint_report.issues

        # === Retry loop: AI fix on FULL document only ===
        while last_issues and attempts < max_attempts:
            attempts += 1
            logger.warning(
                "Lint issues remain (count=%d). AI fix attempt=%d for %s",
                len(last_issues),
                attempts,
                draft_path.name,
            )

            current_text = rewriter.rewrite(
                current_text,
                issues=_collect_issue_strings(last_issues),
                attempt=attempts,
            )

            current_path = pipeline.to_ai_fixed(
                current_path, current_text, attempt=attempts
            )

            current_path, lint_report = run_final_lint(
                current_path=current_path,
                pipeline=pipeline,
            )
            last_issues = lint_report.issues

    else:
        # === Deterministic path ===
        attempts = 1
        current_path, lint_report = run_final_lint(
            current_path=input_path,
            pipeline=pipeline,
        )
        last_issues = lint_report.issues

        if last_issues:
            logger.warning(
                "Found %d lint issues. Running deterministic fixer for %s",
                len(last_issues),
                draft_path.name,
            )
            fr = fix_recipe(draft_path)
            current_text = fr.fixed
            current_path = pipeline.to_ai_fixed(
                input_path, current_text, attempt=attempts
            )
            current_path, lint_report = run_final_lint(
                current_path=current_path,
                pipeline=pipeline,
            )
            last_issues = lint_report.issues
        else:
            current_text = original_text

    # === Final classification ===
    if not last_issues:
        status = "ready"
        final_path = pipeline.to_ready(current_path)
        logger.info("READY: %s", draft_path.name)
    else:
        status = "rejected"
        final_path = pipeline.to_rejected(current_path, _collect_issue_strings(last_issues))
        logger.error(
            "REJECTED: %s (issues=%d)", draft_path.name, len(last_issues)
        )

    fix_result = FixResult(
        path=draft_path,
        original=original_text,
        fixed=current_text,
        actions=[],
    )

    return ProcessOutcome(
        original_path=draft_path,
        final_path=final_path,
        status=status,
        attempts=attempts,
        issues=last_issues,
        fix_result=fix_result,
    )

def enrich_frontmatter_with_ai(
    rewriter: LLMRecipeRewriter,
    markdown: str,
    logger
) -> str:
    logger.info("AI front-matter enrichment started")
    enriched = rewriter.enrich_frontmatter(markdown)
    logger.info("AI front-matter enrichment finished")
    return enriched

def enrich_nutrition_with_ai(
    rewriter,
    markdown: str,
    logger=None,
) -> str:
    """
    Enrich nutritional sections using a dedicated AI prompt.
    This function ONLY fills the nutritional sections
    ("ערכים תזונתיים" and "ויטמינים ומינרלים בולטים")
    and does not modify YAML front matter, ingredients,
    or preparation steps.
    """
    if logger:
        logger.debug("Calling AI nutrition enrichment")

    return rewriter.enrich_nutrition(markdown)


def merge_nutrition_sections(*, original: str, nutrition_block: str) -> str:
    """
    Merge the nutrition markdown block into the full recipe document.
    Replaces the content under '## ערכים תזונתיים (הערכה ל-100 גרם)'
    until the next '##' section or end of file.
    """

    if not nutrition_block.strip():
        return original

    original = original.replace("\r\n", "\n")
    nutrition_block = nutrition_block.strip()

    pattern = re.compile(
        r"(##\s+ערכים\s+תזונתיים[^\n]*\n)(.*?)(?=\n##\s+|\Z)",
        re.DOTALL,
    )

    replacement = r"\1\n" + nutrition_block + "\n"

    new_text, count = pattern.subn(replacement, original, count=1)

    # If nutrition section not found, do not modify document
    if count == 0:
        return original

    return new_text


@click.command(help=HELP_MSG)
@click.option(
    "--drafts-dir",
    type=click.Path(path_type=Path, exists=True, file_okay=False),
    default=Path("_drafts"),
    show_default=True,
    help="Directory containing draft markdown files to process.",
)
@click.option(
    "--use-ai",
    is_flag=True,
    help="Use OpenAI to normalize/fix drafts until they pass lint (bounded by --max-attempts).",
)
@click.option(
    "--model",
    default="gpt-4o-mini",
    show_default=True,
    help="OpenAI model name (used only with --use-ai).",
)
@click.option(
    "--max-attempts",
    type=int,
    default=3,
    show_default=True,
    help="Max total AI attempts per file (1 normalize + fixes). Used only with --use-ai.",
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
    help="Return exit code 1 if any file is rejected or has issues.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Print resolved parameters, PWD, and log location.",
)
def main(
    drafts_dir: Path,
    use_ai: bool,
    model: str,
    max_attempts: int,
    log_level: str,
    dry_run: bool,
    fail_on_issues: bool,
    verbose: bool,
) -> None:
    if max_attempts < 1:
        raise click.ClickException("--max-attempts must be >= 1")

    # Initialize pipeline dirs under drafts_dir
    logger = logging.getLogger(__name__)

    pipeline = StagePipeline(
        base_dir=drafts_dir,
        logger=logging.getLogger("stage_pipeline"),
        dry_run=dry_run,
    )
    pipeline.init_run()

    # Logging
    log_file_path: Optional[Path] = None
    if dry_run:
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
    else:
        setup_logging(
            log_dir=str(pipeline.logs_dir),
            log_name="drafts_checker",
            level=log_level,
        )
        log_files = sorted(pipeline.logs_dir.glob("drafts_checker_*.log"))
        log_file_path = log_files[-1] if log_files else None

    logger = logging.getLogger(__name__)

    if verbose:
        click.echo("=== drafts-checker verbose ===")
        click.echo(f"PWD                : {Path.cwd().resolve()}")
        click.echo(f"drafts_dir         : {drafts_dir.resolve()}")
        click.echo(f"use_ai             : {use_ai}")
        click.echo(f"model              : {model}")
        click.echo(f"max_attempts       : {max_attempts}")
        click.echo(f"log_level          : {log_level}")
        click.echo(f"dry_run            : {dry_run}")
        click.echo(f"fail_on_issues     : {fail_on_issues}")
        click.echo(f"reports_dir        : {_safe_resolve(pipeline.reports_dir)}")
        click.echo(f"logs_dir           : {_safe_resolve(pipeline.logs_dir)}")
        if dry_run:
            click.echo("log_file           : <dry-run: no log file>")
        else:
            click.echo(f"log_file           : {_safe_resolve(log_file_path)}")
        click.echo("================================")

    if dry_run:
        click.echo("DRY-RUN: no files will be created.")
    else:
        click.echo(f"Logs written to: {pipeline.logs_dir.resolve()}")

    logger.info("Starting drafts checker")
    logger.info("Drafts dir: %s", drafts_dir)
    logger.info("Use AI: %s", use_ai)
    logger.info("Model: %s", model)
    logger.info("Max attempts: %d", max_attempts)
    logger.info("Dry run: %s", dry_run)
    if use_ai and not os.getenv("OPENAI_API_KEY"):
        message = "enviroment variable OPENAI_API_KEY is not set, but --use-ai was specified. Please define it in the environment or in a .env file."
        logger.error(message)
        raise click.ClickException(message)         


    # Build AI client (only if requested)
    rewriter: Optional[LLMRecipeRewriter] = None
    if use_ai:
        client = _build_openai_client()
        rewriter = LLMRecipeRewriter(client=client, model=model, logger=logging.getLogger("llm_recipe_rewriter"))

    # Scan drafts
    drafts = scan_recipes(str(drafts_dir))
    if not drafts:
        click.echo("No draft recipes found.")
        logger.info("No draft recipes found. Exiting.")
        raise SystemExit(0)

    outcomes: List[ProcessOutcome] = []
    exit_code = 0

    for draft in drafts:
        logger.info("Processing draft: %s", draft.name)

        outcome = _process_one_draft(
            draft_path=draft,
            pipeline=pipeline,
            rewriter=rewriter,
            use_ai=use_ai,
            max_attempts=max_attempts,
            fail_on_issues=fail_on_issues,
            dry_run=dry_run,
            logger=logger,
        )
        outcomes.append(outcome)

        if fail_on_issues and outcome.status != "ready":
            exit_code = 1

    # Reports
    _write_reports(
        output_dir=pipeline.reports_dir,
        outcomes=outcomes,
        dry_run=dry_run,
        logger=logger,
    )

    # Summary (console)
    ready_count = sum(1 for o in outcomes if o.status == "ready")
    rejected_count = sum(1 for o in outcomes if o.status == "rejected")
    click.echo(f"Summary: ready={ready_count}, rejected={rejected_count}, total={len(outcomes)}")

    logger.info("Drafts checker finished")
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
