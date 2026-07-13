from datetime import datetime, timezone, timedelta

from git_cleaner.app import BranchesContent
from git_cleaner.git_ops import BranchInfo


def test_recent_branch_is_green():
    """Test that recent branches get green color."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature/new",
        commit_date=now - timedelta(days=10),
        is_current=False,
    )
    assert BranchesContent._get_staleness_color(branch.commit_date) == "green"


def test_medium_branch_is_yellow():
    """Test that medium-age branches get yellow color."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature/medium",
        commit_date=now - timedelta(days=45),
        is_current=False,
    )
    assert BranchesContent._get_staleness_color(branch.commit_date) == "yellow"


def test_old_branch_is_red():
    """Test that old branches get red color."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature/old",
        commit_date=now - timedelta(days=100),
        is_current=False,
    )
    assert BranchesContent._get_staleness_color(branch.commit_date) == "red"


def test_exactly_30_days_is_yellow():
    """Test that exactly 30 days is yellow (boundary, < 30 is green)."""
    now = datetime.now(timezone.utc)
    assert BranchesContent._get_staleness_color(now - timedelta(days=30)) == "yellow"


def test_exactly_90_days_is_red():
    """Test that exactly 90 days is red (boundary, < 90 is yellow)."""
    now = datetime.now(timezone.utc)
    assert BranchesContent._get_staleness_color(now - timedelta(days=90)) == "red"
