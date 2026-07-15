"""UI miscellaneous tests: help overlay, batch progress, and health indicators."""

import inspect
from datetime import datetime, timezone, timedelta

from git_cleaner.app import BranchesContent, HelpOverlay, MainScreen
from git_cleaner.git_ops import BranchInfo
from textual.events import Key


# ─── Help overlay ────────────────────────────────────────────────────────────


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
        assert len(widgets) == 1
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


# ─── Batch progress ──────────────────────────────────────────────────────────


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


# ─── Health indicators ───────────────────────────────────────────────────────


def test_health_indicator_method_exists():
    """Test that _get_health_indicator method exists."""
    assert hasattr(BranchesContent, '_get_health_indicator')


def test_current_branch_shows_at():
    """Test that current branch shows @ indicator."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="main",
        commit_date=now,
        is_current=True,
    )
    assert BranchesContent._get_health_indicator(branch) == "@"


def test_ahead_branch_shows_plus():
    """Test that branch ahead of upstream shows +N."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature",
        commit_date=now,
        is_current=False,
        ahead=3,
        has_upstream=True,
    )
    assert BranchesContent._get_health_indicator(branch) == "+3"


def test_behind_branch_shows_minus():
    """Test that branch behind upstream shows -N."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature",
        commit_date=now,
        is_current=False,
        behind=5,
        has_upstream=True,
    )
    assert BranchesContent._get_health_indicator(branch) == "-5"


def test_ahead_and_behind():
    """Test branch both ahead and behind."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature",
        commit_date=now,
        is_current=False,
        ahead=2,
        behind=7,
        has_upstream=True,
    )
    result = BranchesContent._get_health_indicator(branch)
    assert "+2" in result
    assert "-7" in result


def test_current_ahead_and_behind():
    """Test current branch that is also ahead/behind."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature",
        commit_date=now,
        is_current=True,
        ahead=1,
        behind=3,
        has_upstream=True,
    )
    result = BranchesContent._get_health_indicator(branch)
    assert "@" in result
    assert "+1" in result
    assert "-3" in result


def test_healthy_branch_returns_empty():
    """Test branch with no issues returns empty string."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="feature",
        commit_date=now,
        is_current=False,
    )
    assert BranchesContent._get_health_indicator(branch) == ""


def test_in_sync_current_shows_at_only():
    """Test current branch in sync with upstream shows only @."""
    now = datetime.now(timezone.utc)
    branch = BranchInfo(
        name="main",
        commit_date=now,
        is_current=True,
        ahead=0,
        behind=0,
        has_upstream=True,
    )
    assert BranchesContent._get_health_indicator(branch) == "@"
