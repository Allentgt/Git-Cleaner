from datetime import datetime, timezone, timedelta

from git_cleaner.app import BranchesContent
from git_cleaner.git_ops import BranchInfo


def test_health_indicator_method_exists():
    """Test that _get_health_indicator method exists."""
    assert hasattr(BranchesContent, '_get_health_indicator')


def test_current_branch_shows_at():
    """Test that current branch shows @ indicator."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="main",
        commit_date=now,
        is_current=True,
    )
    assert BranchesContent._get_health_indicator(branch) == "@"


def test_ahead_branch_shows_plus():
    """Test that branch ahead of upstream shows +N."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature",
        commit_date=now,
        is_current=False,
        ahead=3,
        has_upstream=True,
    )
    assert BranchesContent._get_health_indicator(branch) == "+3"


def test_behind_branch_shows_minus():
    """Test that branch behind upstream shows -N."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature",
        commit_date=now,
        is_current=False,
        behind=5,
        has_upstream=True,
    )
    assert BranchesContent._get_health_indicator(branch) == "-5"


def test_ahead_and_behind():
    """Test branch both ahead and behind."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature",
        commit_date=now,
        is_current=False,
        ahead=2,
        behind=7,
        has_upstream=True,
    )
    result = BranchesContent._get_health_indicator(branch)
    assert "+2" in result
    assert "-7" in result


def test_current_ahead_and_behind():
    """Test current branch that is also ahead/behind."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature",
        commit_date=now,
        is_current=True,
        ahead=1,
        behind=3,
        has_upstream=True,
    )
    result = BranchesContent._get_health_indicator(branch)
    assert "@" in result
    assert "+1" in result
    assert "-3" in result


def test_healthy_branch_returns_empty():
    """Test branch with no issues returns empty string."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature",
        commit_date=now,
        is_current=False,
    )
    assert BranchesContent._get_health_indicator(branch) == ""


def test_in_sync_current_shows_at_only():
    """Test current branch in sync with upstream shows only @."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="main",
        commit_date=now,
        is_current=True,
        ahead=0,
        behind=0,
        has_upstream=True,
    )
    assert BranchesContent._get_health_indicator(branch) == "@"
