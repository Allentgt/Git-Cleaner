# Logo utilities for git-cleaner
#
# Data source: logo_data.py → LOGO_BYTES (raw ANSI bytes, bitrimus, 0.5x, no shadow)
#
# Exports:
#   LOGO_BYTES — raw ANSI bytes (for CLI splash)
#   SLIM_LOGO  — plain text, further scaled down for TUI banner
import re

from git_cleaner.logo_data import LOGO_BYTES as _RAW


def _strip_ansi(raw: bytes) -> str:
    """Strip ANSI escape codes from raw bytes, return clean UTF-8 text."""
    text = raw.decode("utf-8")
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    text = re.sub(r"\x1b\[\?25[lh]", "", text)
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
    return text


def _scale_block_art(text: str, factor: float) -> str:
    """Nearest-neighbour downscale of block-art text."""
    lines_orig = text.split("\n")
    h_orig = len(lines_orig)
    w_orig = max(len(l) for l in lines_orig)
    h_out = max(1, round(h_orig * factor))
    w_out = max(1, round(w_orig * factor))
    out: list[str] = []
    for r_out in range(h_out):
        r_orig = min(int(r_out / factor + 0.5), h_orig - 1)
        row_orig = lines_orig[r_orig]
        chars: list[str] = []
        for c_out in range(w_out):
            c_orig = min(int(c_out / factor + 0.5), len(row_orig) - 1)
            chars.append(row_orig[c_orig] if c_orig < len(row_orig) else " ")
        out.append("".join(chars).rstrip())
    if out:
        min_lead = min(len(l) - len(l.lstrip()) for l in out)
        return "\n".join(l[min_lead:] for l in out)
    return "\n".join(out)


# Clean full-size text version (5 lines × 69 cols)
CLEAN_LOGO = _strip_ansi(_RAW).rstrip("\n")
