"""Combined filter tests: search + author + age together.

Verifies that the static filter methods compose correctly, matching
the logic in BranchesContent._filtered_branches().
"""
from datetime import datetime, timezone, timedelta

from git_cleaner.app import BranchesContent
from git_cleaner.git_ops import BranchInfo


def _branches():
    """Return a fixed set of branches for filter combination tests."""
    now = datetime.now(timezone.utc)
    return [
        BranchInfo(name="feature/new", commit_date=now - timedelta(days=5), is_current=False, author="Alice"),
        BranchInfo(name="feature/old", commit_date=now - timedelta(days=100), is_current=False, author="Alice"),
        BranchInfo(name="bugfix/new", commit_date=now - timedelta(days=10), is_current=False, author="Bob"),
        BranchInfo(name="bugfix/old", commit_date=now - timedelta(days=90), is_current=False, author="Bob"),
    ]


def _apply(branches, search=None, author=None, max_age_days=None):
    """Apply the same filter pipeline as BranchesContent._filtered_branches."""
    search_re = BranchesContent._compile_search(search)
    result = []
    for b in branches:
        if search_re and not search_re.search(b.name):
            continue
        if author and b.author != author:
            continue
        if not BranchesContent._is_within_age_limit(b.commit_date, max_age_days):
            continue
        result.append(b)
    return result


def test_search_and_age():
    """Search 'feature' + age 30 days → only feature/new."""
    filtered = _apply(_branches(), search="feature", max_age_days=30)
    names = [b.name for b in filtered]
    assert names == ["feature/new"]


def test_author_and_age():
    """Author 'Alice' + age 30 days → only feature/new."""
    filtered = _apply(_branches(), author="Alice", max_age_days=30)
    names = [b.name for b in filtered]
    assert names == ["feature/new"]


def test_search_author_and_age():
    """All three filters: search 'feature', author 'Alice', age 30 → feature/new."""
    filtered = _apply(_branches(), search="feature", author="Alice", max_age_days=30)
    assert len(filtered) == 1
    assert filtered[0].name == "feature/new"


def test_search_and_age_no_match():
    """Search 'bugfix' + author 'Alice' → no match (mismatched search+author)."""
    filtered = _apply(_branches(), search="bugfix", author="Alice")
    assert filtered == []


def test_no_filters_returns_all():
    """No filters → all branches returned."""
    filtered = _apply(_branches())
    assert len(filtered) == 4


def test_age_only_filters_old():
    """Age 30 days, no search/author → keeps only recent branches."""
    filtered = _apply(_branches(), max_age_days=30)
    names = [b.name for b in filtered]
    assert names == ["feature/new", "bugfix/new"]
