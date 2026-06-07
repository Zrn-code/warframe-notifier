"""Logging setup: rotating file handler + console."""

import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(log_file: str, level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if root.handlers:
        return  # already configured
    root.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # No console stream under pythonw (background task) — skip it then.
    if sys.stderr is not None:
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        root.addHandler(console)
