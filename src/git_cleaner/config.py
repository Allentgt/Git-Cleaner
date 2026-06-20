import fnmatch
import tomllib
from pathlib import Path

DEFAULT_PROTECTED = ["main", "master", "develop"]


def _load_toml(path: Path) -> dict:
    if path.exists():
        with open(path, "rb") as f:
            return tomllib.load(f)
    return {}


def get_protected_patterns(repo_path: Path) -> list[str]:
    """Return merged list of protected branch patterns.

    Order of precedence (last wins, but patterns are additive):
    1. Hardcoded defaults (main, master, develop)
    2. Global config ~/.git-branch-cleaner.toml
    3. Project config .git-branch-cleaner.toml
    """
    patterns = list(DEFAULT_PROTECTED)
    for cfg_path in [
        Path.home() / ".git-branch-cleaner.toml",
        repo_path / ".git-branch-cleaner.toml",
    ]:
        cfg = _load_toml(cfg_path)
        patterns.extend(cfg.get("protected", {}).get("patterns", []))
    return patterns


def get_blacklist_patterns(repo_path: Path) -> list[str]:
    """Return merged list of blacklist patterns from global + project config."""
    patterns: list[str] = []
    for cfg_path in [
        Path.home() / ".git-branch-cleaner.toml",
        repo_path / ".git-branch-cleaner.toml",
    ]:
        cfg = _load_toml(cfg_path)
        patterns.extend(cfg.get("blacklist", {}).get("patterns", []))
    return patterns


def matches_any(name: str, patterns: list[str]) -> bool:
    """Check if a branch name matches any of the given fnmatch patterns."""
    return any(fnmatch.fnmatch(name, p) for p in patterns)
