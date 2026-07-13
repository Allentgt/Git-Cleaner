"""Tests for batch delete progress indicator."""

import inspect

from git_cleaner.app import BranchesContent


def test_on_delete_progress_signature():
    """_on_delete_progress accepts (current, total, branch)."""
    sig = inspect.signature(BranchesContent._on_delete_progress)
    params = list(sig.parameters.keys())
    assert params == ["self", "current", "total", "branch"]


def test_on_delete_progress_format():
    """Progress message formats as 'Deleting N/M: branch-name'."""
    source = inspect.getsource(BranchesContent._on_delete_progress)
    assert "Deleting {current}/{total}: {branch}" in source


def test_handle_confirmation_is_async():
    """handle_confirmation must be async to yield to the event loop."""
    source = inspect.getsource(BranchesContent.delete_selected)
    assert "async def handle_confirmation" in source
    assert "await asyncio.sleep(0)" in source
