import tempfile
from pathlib import Path
from git_cleaner.config import get_protected_patterns, get_blacklist_patterns, matches_any


def test_default_protected_patterns():
    """Should include main, master, develop by default with no config files."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        patterns = get_protected_patterns(repo)
        assert "main" in patterns
        assert "master" in patterns
        assert "develop" in patterns


def test_project_config_adds_protected_patterns():
    """Project-level .git-branch-cleaner.toml should add patterns."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        (repo / ".git-branch-cleaner.toml").write_text(
            '[protected]\npatterns = ["release/*"]\n', encoding="utf-8"
        )
        patterns = get_protected_patterns(repo)
        assert "release/*" in patterns


def test_blacklist_returns_empty_when_no_config():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        patterns = get_blacklist_patterns(repo)
        assert patterns == []


def test_blacklist_from_project_config():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        (repo / ".git-branch-cleaner.toml").write_text(
            '[blacklist]\npatterns = ["archive/*"]\n', encoding="utf-8"
        )
        patterns = get_blacklist_patterns(repo)
        assert "archive/*" in patterns


def test_matches_any_exact_match():
    assert matches_any("main", ["main", "master"])


def test_matches_any_wildcard():
    assert matches_any("release/v1.0", ["release/*"])


def test_matches_any_no_match():
    assert not matches_any("feature/x", ["main", "release/*"])
