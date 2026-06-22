# Logo utilities for git-cleaner
#
# Data source: logo_data.py → LOGO_BYTES (raw ANSI bytes, bitrimus, 0.5x, no shadow)
# Text: git-cleaner
#
# Exports:
#   LOGO_BYTES — raw ANSI bytes (for CLI splash)
#   CLEAN_LOGO — plain text (5 lines × 69 cols)
import re

from git_cleaner.logo_data import LOGO_BYTES as _RAW


def _strip_ansi(raw: bytes) -> str:
    """Strip ANSI escape codes from raw bytes, return clean UTF-8 text."""
    text = raw.decode("utf-8")
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    text = re.sub(r"\x1b\[\?25[lh]", "", text)
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
    return text


# Clean full-size text version (5 lines × 69 cols)
CLEAN_LOGO = _strip_ansi(_RAW).rstrip("\n")
