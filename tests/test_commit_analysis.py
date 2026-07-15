"""Tests for Commit Analysis functions."""
import pytest
from pathlib import Path

from git_cleaner.git_ops import (
    CommitInfo,
    AuthorStats,
    get_commit_log,
    get_author_stats,
    get_large_commits,
)


@pytest.fixture
def repo(tmp_path):
    """Create a test git repo with a few commits."""
    import subprocess
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, capture_output=True)
    # Create 5 commits
    for i in range(5):
        (tmp_path / f"file{i}.txt").write_text(f"content {i}\n" * 10)
        subprocess.run(["git", "add", f"file{i}.txt"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"commit {i}"], cwd=tmp_path, capture_output=True)
    return tmp_path


class TestCommitInfo:
    def test_dataclass(self):
        from datetime import datetime, timezone
        c = CommitInfo(short_hash="abc1234", author="test@test.com", date=datetime.now(timezone.utc), subject="test")
        assert c.short_hash == "abc1234"


class TestGetCommitLog:
    def test_returns_commits(self, repo):
        commits = get_commit_log(repo)
        assert len(commits) == 5
        assert all(isinstance(c, CommitInfo) for c in commits)
        assert all(c.author == "test@test.com" for c in commits)

    def test_limit(self, repo):
        commits = get_commit_log(repo, limit=2)
        assert len(commits) == 2

    def test_invalid_ref(self, repo):
        commits = get_commit_log(repo, ref="nonexistent")
        assert commits == []


class TestGetAuthorStats:
    def test_returns_stats(self, repo):
        stats = get_author_stats(repo)
        assert len(stats) == 1
        assert stats[0].author == "test@test.com"
        assert stats[0].commits == 5
        assert stats[0].insertions > 0


class TestGetLargeCommits:
    def test_returns_large_commits(self, repo):
        # Each commit adds 1 file, threshold=0 → should find all
        large = get_large_commits(repo, threshold=0)
        assert len(large) == 5

    def test_high_threshold(self, repo):
        # threshold=5, each commit has 1 file → none qualify
        large = get_large_commits(repo, threshold=5)
        assert len(large) == 0
