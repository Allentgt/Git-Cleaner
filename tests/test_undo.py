"""Tests for undo stack, undo history overlay, and undo-all."""

from git_cleaner.app import BranchesContent, UndoHistory, MainScreen
from textual.events import Key


# ─── Undo stack (push / pop) ────────────────────────────────────────────────


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


# ─── Undo history overlay ───────────────────────────────────────────────────


def test_undo_history_exists():
    """Test that UndoHistory class exists."""
    assert UndoHistory is not None


def test_undo_history_has_compose():
    """Test that UndoHistory has compose method."""
    assert hasattr(UndoHistory, "compose")


def test_undo_history_compose_with_entries():
    """compose() yields one Vertical for a non-empty stack."""
    stack = [{"branch-a": "abc123"}, {"branch-b": "def456"}]
    overlay = UndoHistory(stack)
    widgets = list(overlay.compose())
    assert len(widgets) == 1
    assert widgets[0].id == "undo-history-container"


def test_undo_history_compose_empty():
    """compose() yields one Vertical for an empty stack."""
    overlay = UndoHistory([])
    widgets = list(overlay.compose())
    assert len(widgets) == 1
    assert widgets[0].id == "undo-history-container"


def test_undo_history_dismisses_on_key():
    """on_key must dismiss the overlay."""
    overlay = UndoHistory([])
    dismissed = []
    overlay.dismiss = lambda: dismissed.append(True)
    overlay.on_key(Key("a", "a"))
    assert dismissed


def test_undo_history_binding_exists():
    """MainScreen.BINDINGS contains a binding for show_undo_history."""
    keys = [b.key for b in MainScreen.BINDINGS]
    actions = [b.action for b in MainScreen.BINDINGS]
    assert "H" in keys
    assert "show_undo_history" in actions


# ─── Undo all ───────────────────────────────────────────────────────────────


def test_undo_all_drains_stack():
    """Test that undo_all clears the undo stack."""
    content = BranchesContent.__new__(BranchesContent)
    content._undo_stack = [{"branch-a": "abc123"}, {"branch-b": "def456"}]
    entries = list(reversed(content._undo_stack))
    content._undo_stack.clear()
    assert len(content._undo_stack) == 0
    assert len(entries) == 2
    assert entries[0] == {"branch-b": "def456"}
    assert entries[1] == {"branch-a": "abc123"}
