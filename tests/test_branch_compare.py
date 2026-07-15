from pathlib import Path
from git_cleaner.git_ops import get_diff_stat, get_merge_base, get_commits_between


def test_compare_content_exists():
    """CompareContent class exists."""
    from git_cleaner.app import CompareContent
    assert CompareContent is not None


def test_get_merge_base_returns_sha():
    """merge-base returns a 40-char hex SHA."""
    import subprocess
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=Path("."),
    )
    head = result.stdout.strip()
    base = get_merge_base(Path("."), "HEAD", "HEAD")
    assert base == head


def test_get_diff_stat_returns_list():
    """diff stat returns list of (added, removed, path) tuples."""
    stats = get_diff_stat(Path("."), "HEAD", "HEAD")
    assert isinstance(stats, list)


def test_get_commits_between_returns_list():
    """commits between identical refs is empty."""
    commits = get_commits_between(Path("."), "HEAD", "HEAD")
    assert commits == []
