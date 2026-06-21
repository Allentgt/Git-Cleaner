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
    """Persist the theme name to the global config file.

    Only touches the [theme] section — all other sections are left as-is.
    """
    if not _GLOBAL_CFG.exists():
        _GLOBAL_CFG.write_text(f'[theme]\nname = "{theme_name}"\n')
        return

    lines = _GLOBAL_CFG.read_text().splitlines()
    out: list[str] = []
    in_theme_section = False
    theme_found = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            # Section boundary
            section_name = stripped[1:-1].strip()
            if section_name == "theme":
                in_theme_section = True
                theme_found = True
                out.append("[theme]")
                continue
            else:
                in_theme_section = False
                out.append(line)
                continue

        if in_theme_section:
            # Skip existing theme lines, we'll write our own
            if stripped.startswith("name") or stripped.startswith("name "):
                continue
            if stripped == "":
                continue
            out.append(line)
        else:
            out.append(line)

    # Append or update the theme section
    if theme_found:
        out.append(f'name = "{theme_name}"')
    else:
        out.append("")
        out.append('[theme]')
        out.append(f'name = "{theme_name}"')

    _GLOBAL_CFG.write_text("\n".join(out) + "\n")
