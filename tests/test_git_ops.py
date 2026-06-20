import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

from git_cleaner.git_ops import (
    get_repo_root,
    list_branches,
    delete_branches,
    delete_remote_branches,
    BranchInfo,
    get_git_dir_size,
    get_object_stats,
    run_gc,
    repack_objects,
    prune_remote,
    expire_reflog,
)


def _init_git_repo(path: Path) -> None:
    """Initialize a git repo with some branches for testing."""
    subprocess.run(
        ["git", "init", "-b", "main"], cwd=path, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=path, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"], cwd=path, capture_output=True
    )
    # Create initial commit on main
    (path / "README.md").write_text("# test")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, capture_output=True)
    # Create a feature branch
    subprocess.run(["git", "checkout", "-b", "feature/test"], cwd=path, capture_output=True)
    (path / "feature.txt").write_text("feature")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feature"], cwd=path, capture_output=True)
    # Go back to main and add another commit so main~1 exists
    subprocess.run(["git", "checkout", "main"], cwd=path, capture_output=True)
    (path / "main-update.txt").write_text("update")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "main update"], cwd=path, capture_output=True)
    # Create an old branch from the previous commit on main
    subprocess.run(["git", "branch", "old/experiment", "main~1"], cwd=path, capture_output=True)


def test_get_repo_root():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        root = get_repo_root(repo)
        assert root.resolve() == repo.resolve()


def test_get_repo_root_not_a_repo():
    with tempfile.TemporaryDirectory() as tmp:
        import pytest

        with pytest.raises(RuntimeError, match="Not a git repository"):
            get_repo_root(Path(tmp))


def test_list_branches():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        branches = list_branches(repo)
        names = {b.name for b in branches}
        assert "main" in names
        assert "feature/test" in names
        assert "old/experiment" in names


def test_list_branches_marks_current():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        branches = list_branches(repo)
        current = [b for b in branches if b.is_current]
        assert len(current) == 1
        assert current[0].name == "main"


def test_list_branches_date_filter():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        # Filter with a future date — should return all (everything is in the past)
        future = datetime.now(timezone.utc) + timedelta(days=365)
        branches = list_branches(repo, until=future)
        assert len(branches) > 0
        # Filter with a very old 'since' date — should return all
        past = datetime.fromtimestamp(0, tz=timezone.utc)
        branches = list_branches(repo, since=past)
        assert len(branches) > 0


def test_delete_branches():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        failed = delete_branches(repo, ["old/experiment"])
        assert failed == []
        branches = list_branches(repo)
        assert "old/experiment" not in {b.name for b in branches}


def test_delete_branches_protected_fails():
    """Deleting current branch should fail."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        failed = delete_branches(repo, ["main"])
        assert "main" in failed  # can't delete checked-out branch


def test_delete_remote_branches_fails_without_remote():
    """delete_remote_branches should fail when there's no remote configured."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        # No remote configured, so push --delete should fail
        failed = delete_remote_branches(repo, ["old/experiment"])
        assert "old/experiment" in failed


def test_branch_info_dataclass():
    dt = datetime.now(timezone.utc)
    b = BranchInfo(
        name="test",
        commit_date=dt,
        is_current=True,
        is_protected=False,
        is_blacklisted=True,
    )
    assert b.name == "test"
    assert b.is_current
    assert b.is_blacklisted
    assert not b.is_protected


# ─── Repository health & maintenance ─────────────────────────────────────────


def test_get_git_dir_size():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        size = get_git_dir_size(repo)
        assert isinstance(size, str)
        assert size  # non-empty, e.g. "1.5 KB"


def test_get_object_stats():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        stats = get_object_stats(repo)
        assert "count" in stats
        assert "size" in stats
        assert "in-pack" in stats
        assert "packs" in stats
        assert "size-pack" in stats


def test_run_gc():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        success, msg = run_gc(repo)
        assert success, msg
        assert "GC completed" in msg


def test_run_gc_aggressive():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        success, msg = run_gc(repo, aggressive=True)
        assert success, msg
        assert "GC (aggressive)" in msg


def test_repack_objects():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        # Run gc first to create pack files
        run_gc(repo)
        success, msg = repack_objects(repo)
        assert success, msg
        assert "Repack" in msg


def test_prune_remote_fails_without_remote():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        success, msg = prune_remote(repo)
        assert not success
        # Should mention that origin doesn't exist or similar error
        assert msg


def test_expire_reflog():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_git_repo(repo)
        success, msg = expire_reflog(repo, days=1)
        assert success, msg
        assert "expired" in msg
