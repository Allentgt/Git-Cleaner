from git_cleaner.app import BranchesContent
from git_cleaner.git_ops import BranchInfo
from datetime import datetime, timezone, timedelta


def test_protected_branch_badge():
    """Protected branch gets 'protected' badge."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(name="release/1.0", commit_date=now, is_current=False, is_protected=True)
    assert BranchesContent._get_status_badge(branch) == "protected"


def test_blacklisted_branch_badge():
    """Blacklisted branch gets 'blacklisted' badge."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(name="archive/old", commit_date=now, is_current=False, is_blacklisted=True)
    assert BranchesContent._get_status_badge(branch) == "blacklisted"


def test_multiple_badges():
    """Branch with multiple classifications gets combined badge."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(name="main", commit_date=now, is_current=False, is_protected=True, is_blacklisted=True)
    result = BranchesContent._get_status_badge(branch)
    assert "protected" in result
    assert "blacklisted" in result


def test_no_badge_for_plain_branch():
    """Normal branch with no special status gets empty string."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(name="feature/foo", commit_date=now, is_current=False)
    assert BranchesContent._get_status_badge(branch) == ""
