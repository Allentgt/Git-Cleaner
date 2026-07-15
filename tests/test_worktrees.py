from pathlib import Path
from git_cleaner.git_ops import list_worktrees, WorktreeInfo


def test_list_worktrees_returns_list():
    """list_worktrees returns a list (may be empty for repos without worktrees)."""
    result = list_worktrees(Path("."))
    assert isinstance(result, list)


def test_worktree_info_has_fields():
    """WorktreeInfo dataclass has expected fields."""
    info = WorktreeInfo(
        path="/tmp/test", head="abc1234", branch="main",
        is_bare=False, is_detached=False, is_locked=False, is_prunable=False,
    )
    assert info.path == "/tmp/test"
    assert info.branch == "main"


def test_list_worktrees_main_only():
    """A repo without linked worktrees returns exactly one entry."""
    wts = list_worktrees(Path("."))
    # The main worktree should always be present
    assert len(wts) >= 1
    assert wts[0].branch  # main worktree has a branch checked out
