import fnmatch
import tomllib
from pathlib import Path

DEFAULT_PROTECTED = ["main", "master", "develop"]

_GLOBAL_CFG = Path.home() / ".git-branch-cleaner.toml"


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
        _GLOBAL_CFG,
        repo_path / ".git-branch-cleaner.toml",
    ]:
        cfg = _load_toml(cfg_path)
        patterns.extend(cfg.get("protected", {}).get("patterns", []))
    return patterns


def get_blacklist_patterns(repo_path: Path) -> list[str]:
    """Return merged list of blacklist patterns from global + project config."""
    patterns: list[str] = []
    for cfg_path in [
        _GLOBAL_CFG,
        repo_path / ".git-branch-cleaner.toml",
    ]:
        cfg = _load_toml(cfg_path)
        patterns.extend(cfg.get("blacklist", {}).get("patterns", []))
    return patterns


def matches_any(name: str, patterns: list[str]) -> bool:
    """Check if a branch name matches any of the given fnmatch patterns."""
    return any(fnmatch.fnmatch(name, p) for p in patterns)


# ── Theme persistence ───────────────────────────────────────────────────

_DEFAULT_THEME = "textual-dark"


def load_theme() -> str:
    """Return the saved theme name, or the default."""
    cfg = _load_toml(_GLOBAL_CFG)
    return cfg.get("theme", {}).get("name", _DEFAULT_THEME)


def save_theme(theme_name: str) -> None:
    """Persist the theme name to the global config file."""
    lines = _GLOBAL_CFG.read_text().splitlines() if _GLOBAL_CFG.exists() else []
    out: list[str] = []
    in_theme = False
    for line in lines:
        s = line.strip()
        if s == "[theme]":
            in_theme = True
            continue
        if s.startswith("["):
            in_theme = False
        if not in_theme:
            out.append(line)
    out += ["", "[theme]", f'name = "{theme_name}"']
    _GLOBAL_CFG.write_text("\n".join(out) + "\n")


# ── Repository bookmarks ────────────────────────────────────────────────


def load_bookmarks() -> list[str]:
    """Return list of bookmarked repo paths from global config."""
    cfg = _load_toml(_GLOBAL_CFG)
    return cfg.get("bookmarks", {}).get("paths", [])


def save_bookmarks(bookmarks: list[str]) -> None:
    """Persist bookmarks to the global config file."""
    lines = _GLOBAL_CFG.read_text().splitlines() if _GLOBAL_CFG.exists() else []
    out: list[str] = []
    in_section = False
    for line in lines:
        s = line.strip()
        if s == "[bookmarks]":
            in_section = True
            continue
        if s.startswith("["):
            in_section = False
        if not in_section:
            out.append(line)
    quoted = [f"'{p}'" for p in bookmarks]
    out += ["", "[bookmarks]", f"paths = [{', '.join(quoted)}]"]
    _GLOBAL_CFG.write_text("\n".join(out) + "\n")


def add_bookmark(path: str) -> None:
    """Add a repo path to bookmarks if not already present."""
    bookmarks = load_bookmarks()
    if path not in bookmarks:
        bookmarks.append(path)
        save_bookmarks(bookmarks)


def remove_bookmark(path: str) -> None:
    """Remove a repo path from bookmarks."""
    bookmarks = load_bookmarks()
    bookmarks = [p for p in bookmarks if p != path]
    save_bookmarks(bookmarks)
