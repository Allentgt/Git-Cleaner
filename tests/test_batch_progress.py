"""Tests for batch delete progress indicator."""

from git_cleaner.app import BranchesContent


def test_progress_callback_exists():
    """Test that _on_delete_progress method exists."""
    assert hasattr(BranchesContent, '_on_delete_progress')
