import subprocess
from pathlib import Path

from git_cleaner.app import BranchesContent
from git_cleaner.git_ops import list_branches


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


# ─── Unit tests: _compile_search ─────────────────────────────────────────────


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
    # Should match a string containing the literal "[invalid"
    assert compiled.search("some-[invalid]-branch")
    # Should NOT match without the bracket
    assert not compiled.search("invalid-branch")


def test_compile_search_is_case_insensitive():
    """Compiled pattern is case-insensitive."""
    compiled = BranchesContent._compile_search("feature")
    assert compiled.search("FEATURE/auth")
    assert compiled.search("Feature/main")


# ─── Integration tests: real git repos ───────────────────────────────────────


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
    # No git branch name can contain '[', so literal fallback finds nothing
    assert matched == set()


def test_regex_search_invalid_pattern_fallback_deterministic(tmp_path):
    """Invalid regex fallback produces a working (escaped) pattern, not an exception."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    _init_git_repo(repo, ["feature/auth", "main"])

    branches = list_branches(repo)

    # Various invalid regex patterns — none should raise
    for bad_pattern in ["[invalid", "(unclosed", ")*+{2,}"]:
        compiled = BranchesContent._compile_search(bad_pattern)
        assert compiled is not None
        # Should not raise — just safely filter (likely zero matches)
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
