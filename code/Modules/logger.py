"""
Application-wide logging configuration.

This module provides a single entry point for configuring logging
based on application configuration values.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


class LoggerError(Exception):
    """Raised when logging configuration fails."""
    pass


def setup_logging(
    log_dir: str,
    log_name: str = "application",
    level: str = "INFO",
    rotate: bool = False,
    max_size_mb: int = 5,
    backups: int = 3,
) -> None:
    """
    Configure application-wide logging.

    Responsibilities:
    - Create log directory if it does not exist
    - Configure file and console handlers
    - Apply log level and formatting

    Args:
        log_dir: Directory where log files are written
        level: Logging level (e.g. INFO, DEBUG)
        rotate: Enable log rotation
        max_size_mb: Maximum log file size before rotation
        backups: Number of rotated log files to keep

    Raises:
        LoggerError: If the log directory cannot be created
    """

    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception as exc:
        raise LoggerError(f"Failed to create log directory: {log_dir}") from exc

    log_level = getattr(logging, level.upper(), None)
    if not isinstance(log_level, int):
        raise LoggerError(f"Invalid log level: {level}")

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Close and clear existing handlers (important on Windows)
    for handler in list(root_logger.handlers):
        try:
            handler.close()
        finally:
            root_logger.removeHandler(handler)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{log_name}_{timestamp}.log")

    if rotate:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backups,
            encoding="utf-8",
        )
    else:
        file_handler = logging.FileHandler(
            log_file,
            encoding="utf-8",
        )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    root_logger.addHandler(file_handler)

    # הוסף console handler רק אם לא רצים בטסטים
    if not os.environ.get("UNITTEST"):
        root_logger.addHandler(console_handler)
