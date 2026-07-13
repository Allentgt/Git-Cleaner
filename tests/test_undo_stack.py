"""Tests for the multi-level undo stack."""

from git_cleaner.app import BranchesContent


def test_undo_stack_push():
    """Test that push adds entry to undo stack."""
    content = BranchesContent.__new__(BranchesContent)
    content._undo_stack = []

    entry = {"branch": "test", "remote": False, "parent": None}
    content._push_undo(entry)

    assert len(content._undo_stack) == 1
    assert content._undo_stack[0] == entry


def test_undo_stack_pop():
    """Test that pop removes and returns last entry."""
    content = BranchesContent.__new__(BranchesContent)
    content._undo_stack = [
        {"branch": "first", "remote": False, "parent": None},
        {"branch": "second", "remote": False, "parent": None},
    ]

    entry = content._pop_undo()

    assert entry["branch"] == "second"
    assert len(content._undo_stack) == 1


def test_undo_stack_pop_empty():
    """Test that popping an empty stack returns None."""
    content = BranchesContent.__new__(BranchesContent)
    content._undo_stack = []

    assert content._pop_undo() is None
