from datetime import datetime, timezone, timedelta

from git_cleaner.app import BranchesContent
from git_cleaner.git_ops import BranchInfo


def test_within_age_limit_recent_branch():
    """Branch committed 10 days ago is within a 30-day limit."""
    now = datetime.now(timezone.utc)
    assert BranchesContent._is_within_age_limit(now - timedelta(days=10), 30)


def test_within_age_limit_exact_boundary():
    """Branch committed exactly 30 days ago is within a 30-day limit (<=)."""
    now = datetime.now(timezone.utc)
    assert BranchesContent._is_within_age_limit(now - timedelta(days=30), 30)


def test_within_age_limit_excludes_old_branch():
    """Branch committed 31 days ago is excluded by a 30-day limit."""
    now = datetime.now(timezone.utc)
    assert not BranchesContent._is_within_age_limit(now - timedelta(days=31), 30)


def test_within_age_limit_none_means_no_filter():
    """None max_age_days means no filtering."""
    now = datetime.now(timezone.utc)
    assert BranchesContent._is_within_age_limit(now - timedelta(days=9999), None)


def test_within_age_limit_zero_means_no_filter():
    """Zero max_age_days means no filtering (matches blank select)."""
    now = datetime.now(timezone.utc)
    assert BranchesContent._is_within_age_limit(now - timedelta(days=9999), 0)


def test_within_age_limit_filters_multiple_branches():
    """Filtering a list of branches keeps only those within the age limit."""
    now = datetime.now(timezone.utc)
    branches = [
        BranchInfo(name="recent", commit_date=now - timedelta(days=5), is_current=False),
        BranchInfo(name="boundary", commit_date=now - timedelta(days=30), is_current=False),
        BranchInfo(name="old", commit_date=now - timedelta(days=60), is_current=False),
        BranchInfo(name="ancient", commit_date=now - timedelta(days=365), is_current=False),
    ]
    max_age_days = 30
    included = [b for b in branches if BranchesContent._is_within_age_limit(b.commit_date, max_age_days)]
    names = [b.name for b in included]
    assert "recent" in names
    assert "boundary" in names
    assert "old" not in names
    assert "ancient" not in names


def test_within_age_limit_no_filter_includes_all():
    """With no filter, all branches are included."""
    now = datetime.now(timezone.utc)
    branches = [
        BranchInfo(name="new", commit_date=now - timedelta(days=1), is_current=False),
        BranchInfo(name="old", commit_date=now - timedelta(days=500), is_current=False),
    ]
    included = [b for b in branches if BranchesContent._is_within_age_limit(b.commit_date, None)]
    assert len(included) == 2
