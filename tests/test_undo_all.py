"""Tests for undo all feature."""

from git_cleaner.app import BranchesContent


def test_undo_all_method_exists():
    """Test that undo_all method exists."""
    assert hasattr(BranchesContent, 'undo_all')
