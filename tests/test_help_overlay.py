from git_cleaner.app import HelpOverlay


def test_help_overlay_exists():
    """Test that HelpOverlay class exists."""
    assert HelpOverlay is not None


def test_help_overlay_has_keybindings():
    """Test that help overlay has compose method."""
    assert hasattr(HelpOverlay, "compose")
