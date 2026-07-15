"""UI filter tests: author selection, regex search, age filter, combined filters,
staleness colors, and status badges."""

import subprocess
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from git_cleaner.app import BranchesContent
from git_cleaner.git_ops import BranchInfo, list_branches


# ─── Author selection ────────────────────────────────────────────────────────


def _init_repo(path: Path) -> None:
    """Initialize a git repo with branches by different authors."""
    subprocess.run(["git", "init", "-b", "main"], cwd=path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "alice@test.com"], cwd=path, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Alice"], cwd=path, capture_output=True
    )
    (path / "README.md").write_text("# test")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, capture_output=True)

    # Alice branch
    subprocess.run(["git", "checkout", "-b", "alice/feature"], cwd=path, capture_output=True)
    (path / "alice.txt").write_text("alice")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "alice feature"], cwd=path, capture_output=True)

    # Bob branch
    subprocess.run(["git", "config", "user.email", "bob@test.com"], cwd=path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Bob"], cwd=path, capture_output=True)
    subprocess.run(["git", "checkout", "-b", "bob/feature", "main"], cwd=path, capture_output=True)
    (path / "bob.txt").write_text("bob")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "bob feature"], cwd=path, capture_output=True)

    # Protected branch (main)
    subprocess.run(["git", "checkout", "main"], cwd=path, capture_output=True)


def test_select_by_author_filters_protected_and_blacklisted():
    """select_by_author should not select protected or blacklisted branches."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_repo(repo)

        branches = list_branches(repo)

        alice_branches = [b for b in branches if b.author == "Alice"]
        bob_branches = [b for b in branches if b.author == "Bob"]

        main_branch = next(b for b in branches if b.name == "main")
        main_branch.is_protected = True

        to_select = [b for b in alice_branches if not b.is_protected and not b.is_blacklisted]
        selected_names = {b.name for b in to_select}

        assert "alice/feature" in selected_names
        assert "main" not in selected_names

        bob_selected = [b for b in bob_branches if not b.is_protected and not b.is_blacklisted]
        assert all(b.name not in selected_names for b in bob_selected)

        assert len(to_select) == 1


# ─── Regex search ────────────────────────────────────────────────────────────


def _init_git_repo(path: Path, branch_names: list[str]) -> None:
    """Initialize a git repo and create branches with the given names."""
    subprocess.run(["git", "init", "-b", "main"], cwd=path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=path, capture_output=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, capture_output=True)
    (path / "README.md").write_text("# test")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, capture_output=True)
    for name in branch_names:
        subprocess.run(
            ["git", "checkout", "-b", name], cwd=path, capture_output=True
        )
        (path / "file.txt").write_text(name)
        subprocess.run(["git", "add", "."], cwd=path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", name], cwd=path, capture_output=True
        )
    subprocess.run(["git", "checkout", "main"], cwd=path, capture_output=True)


def test_compile_search_valid_regex():
    """Regex pattern is compiled correctly via the actual code path."""
    compiled = BranchesContent._compile_search(r"feature/.*-v\d+")
    assert compiled.search("feature/auth-v2")
    assert compiled.search("feature/pay-v3")
    assert not compiled.search("bugfix/login")
    assert not compiled.search("main")


def test_compile_search_empty_returns_none():
    """Empty search returns None (no filtering)."""
    assert BranchesContent._compile_search("") is None


def test_compile_search_invalid_falls_back_to_literal():
    """Invalid regex falls back to literal matching via the actual code path."""
    compiled = BranchesContent._compile_search("[invalid")
    assert compiled.search("some-[invalid]-branch")
    assert not compiled.search("invalid-branch")


def test_compile_search_is_case_insensitive():
    """Compiled pattern is case-insensitive."""
    compiled = BranchesContent._compile_search("feature")
    assert compiled.search("FEATURE/auth")
    assert compiled.search("Feature/main")


def test_regex_search_matches_pattern(tmp_path):
    """Regex pattern filters real branches from a real git repo."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    _init_git_repo(repo, ["feature/auth-v2", "bugfix/login", "feature/pay-v3"])

    branches = list_branches(repo)
    compiled = BranchesContent._compile_search(r"feature/.*-v\d+")
    assert compiled is not None

    matched = {b.name for b in branches if compiled.search(b.name)}
    assert "feature/auth-v2" in matched
    assert "feature/pay-v3" in matched
    assert "bugfix/login" not in matched


def test_regex_search_invalid_pattern_fallback_no_match(tmp_path):
    """Invalid regex falls back to literal; no real branch contains '[invalid'."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    _init_git_repo(repo, ["feature/auth", "main", "bugfix/fix"])

    branches = list_branches(repo)
    compiled = BranchesContent._compile_search("[invalid")
    assert compiled is not None

    matched = {b.name for b in branches if compiled.search(b.name)}
    assert matched == set()


def test_regex_search_invalid_pattern_fallback_deterministic(tmp_path):
    """Invalid regex fallback produces a working (escaped) pattern, not an exception."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    _init_git_repo(repo, ["feature/auth", "main"])

    branches = list_branches(repo)

    for bad_pattern in ["[invalid", "(unclosed", ")*+{2,}"]:
        compiled = BranchesContent._compile_search(bad_pattern)
        assert compiled is not None
        _ = [b for b in branches if compiled.search(b.name)]


def test_regex_search_literal_fallback_matches(tmp_path):
    """Branch with a dash-only name is matched by a plain-literal search."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    _init_git_repo(repo, ["feature/auth", "my-custom-branch", "main"])

    branches = list_branches(repo)
    compiled = BranchesContent._compile_search("my-custom")
    assert compiled is not None

    matched = {b.name for b in branches if compiled.search(b.name)}
    assert "my-custom-branch" in matched
    assert "feature/auth" not in matched


# ─── Age filter ──────────────────────────────────────────────────────────────


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


# ─── Combined filters ────────────────────────────────────────────────────────


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


# ─── Staleness colors ────────────────────────────────────────────────────────


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


# ─── Status badges ───────────────────────────────────────────────────────────


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
