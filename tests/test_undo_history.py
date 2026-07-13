from git_cleaner.app import UndoHistory, MainScreen


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
    from textual.events import Key
    overlay.on_key(Key("a", "a"))
    assert dismissed


def test_undo_history_binding_exists():
    """MainScreen.BINDINGS contains a binding for show_undo_history."""
    keys = [b.key for b in MainScreen.BINDINGS]
    actions = [b.action for b in MainScreen.BINDINGS]
    assert "shift+h" in keys
    assert "show_undo_history" in actions
