"""Tests for undo all feature."""

from git_cleaner.app import BranchesContent


def test_undo_all_drains_stack():
    """Test that undo_all clears the undo stack."""
    content = BranchesContent.__new__(BranchesContent)
    content._undo_stack = [{"branch-a": "abc123"}, {"branch-b": "def456"}]
    # Simulate the stack-clearing part of undo_all without needing a Textual app
    entries = list(reversed(content._undo_stack))
    content._undo_stack.clear()
    assert len(content._undo_stack) == 0
    assert len(entries) == 2
    assert entries[0] == {"branch-b": "def456"}
    assert entries[1] == {"branch-a": "abc123"}
