from unittest.mock import patch

from git_cleaner.app import HelpOverlay, MainScreen
from textual.events import Key


def test_help_overlay_compose_yields_one_vertical():
    """compose() yields exactly one Vertical."""
    overlay = HelpOverlay()
    widgets = list(overlay.compose())
    assert len(widgets) == 1
    assert widgets[0].id == "help-container"


def test_help_overlay_uses_bindings_not_hardcoded():
    """compose() iterates MainScreen.BINDINGS; changing them doesn't crash."""
    overlay = HelpOverlay()
    original = MainScreen.BINDINGS

    MainScreen.BINDINGS = [
        type("B", (), {"key": "x", "description": "X-ray"})(),
        type("B", (), {"key": "question", "description": "Help"})(),
    ]
    try:
        widgets = list(overlay.compose())
        assert len(widgets) == 1  # still yields one Vertical
        assert widgets[0].id == "help-container"
    finally:
        MainScreen.BINDINGS = original


def test_help_overlay_dismisses_on_key():
    """on_key must dismiss the overlay."""
    overlay = HelpOverlay()
    dismissed = []
    overlay.dismiss = lambda: dismissed.append(True)
    overlay.on_key(Key("a", "a"))
    assert dismissed


def test_format_key():
    """_format_key wraps the key in brackets."""
    assert HelpOverlay._format_key("ctrl+r") == "[ctrl+r]"
    assert HelpOverlay._format_key("space") == "[space]"
