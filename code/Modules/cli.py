"""
Command-line interface for the recipe tool.

This module wires together configuration, logging, scanning,
linting, fixing, diff generation, and reporting.
"""

import logging
from pathlib import Path

import click

from Modules.config import Config
from Modules.logger import setup_logging
from Modules.scanner import scan_recipes
from Modules.linter import lint_recipe
from Modules.fixer import fix_recipe
from Modules.diff_html import generate_diff_html
from Modules.report import write_file_report, write_index_report


def run(config_dict: dict) -> None:
    """
    Execute the recipe tool pipeline.

    Args:
        config_dict: Configuration dictionary
    """

    config = Config(config_dict)

    if config.logging.enabled:
        setup_logging(
            log_dir=config.logging.dir,
            log_name="application",
            level=config.logging.level,
            rotate=config.logging.rotate,
            max_size_mb=config.logging.max_size_mb,
            backups=config.logging.backups,
        )

    logger = logging.getLogger(__name__)
    logger.info("Starting recipe tool")

    recipes_dir = Path(config.paths.recipes_dir)
    fixed_dir = Path(config.paths.fixed_dir)
    reports_dir = Path(config.paths.reports_dir)

    fixed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    recipe_files = scan_recipes(str(recipes_dir))
    logger.info("Found %d recipe files", len(recipe_files))

    report_paths = []
    fix_results = []

    for recipe_path in recipe_files:
        logger.info("Processing %s", recipe_path.name)

        lint_result = lint_recipe(recipe_path)
        fix_result = fix_recipe(recipe_path)

        if fix_result.changed:
            target = fixed_dir / recipe_path.name
            target.write_text(fix_result.fixed, encoding="utf-8")
            logger.info("Written fixed file to %s", target)

        diff_html = generate_diff_html(
            fix_result.original,
            fix_result.fixed,
            highlight_color=config.report.highlight_color,
        )

        report_path = write_file_report(
            output_dir=reports_dir,
            fix_result=fix_result,
            diff_html=diff_html,
        )

        report_paths.append(report_path)
        fix_results.append(fix_result)

    write_index_report(
        output_dir=reports_dir,
        reports=report_paths,
        results=fix_results,
    )

    logger.info("Recipe tool finished successfully")


@click.command(help="Recipe Markdown Lint & Fix Tool")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to Python config file defining CONFIG dict",
)
def main(config_path: Path) -> None:
    """
    CLI entry point.
    """

    namespace = {}
    exec(config_path.read_text(encoding="utf-8"), namespace)

    if "CONFIG" not in namespace:
        raise click.ClickException(
            "Config file must define a CONFIG dictionary"
        )

    run(namespace["CONFIG"])


if __name__ == "__main__":
    main()
