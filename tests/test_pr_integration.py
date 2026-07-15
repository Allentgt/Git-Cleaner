"""Tests for PR/MR Integration functions."""
import pytest
from pathlib import Path

from git_cleaner.git_ops import (
    PRInfo,
    _detect_provider,
    _get_api_token,
    _get_api_repo,
    list_open_prs,
    get_pr_for_branch,
)


class TestPRInfo:
    def test_dataclass(self):
        pr = PRInfo(number=1, title="Test PR", state="open", url="https://example.com", author="user", branch="feat")
        assert pr.number == 1
        assert pr.state == "open"


class TestProviderDetection:
    def test_no_remote(self, tmp_path):
        assert _detect_provider(tmp_path) is None

    def test_github(self, tmp_path):
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", "git@github.com:user/repo.git"], cwd=tmp_path, capture_output=True)
        assert _detect_provider(tmp_path) == "github"

    def test_gitlab(self, tmp_path):
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", "git@gitlab.com:user/repo.git"], cwd=tmp_path, capture_output=True)
        assert _detect_provider(tmp_path) == "gitlab"


class TestAPIRepo:
    def test_github_ssh(self, tmp_path):
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", "git@github.com:user/repo.git"], cwd=tmp_path, capture_output=True)
        assert _get_api_repo(tmp_path, "github") == "user/repo"

    def test_github_https(self, tmp_path):
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/user/repo.git"], cwd=tmp_path, capture_output=True)
        assert _get_api_repo(tmp_path, "github") == "user/repo"

    def test_gitlab_url_encoded(self, tmp_path):
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", "git@gitlab.com:group/subgroup/repo.git"], cwd=tmp_path, capture_output=True)
        result = _get_api_repo(tmp_path, "gitlab")
        assert result == "group%2Fsubgroup%2Frepo"


class TestListOpenPRs:
    def test_no_remote(self, tmp_path):
        assert list_open_prs(tmp_path) == []

    def test_no_token(self, tmp_path):
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", "git@github.com:user/repo.git"], cwd=tmp_path, capture_output=True)
        assert list_open_prs(tmp_path) == []
