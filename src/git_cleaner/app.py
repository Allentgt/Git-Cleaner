import asyncio
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header,
    Footer,
    Button,
    Label,
    Static,
    DataTable,
    LoadingIndicator,
    RichLog,
)
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual.widgets._footer import Footer as FooterBase
from textual_timepiece.pickers import DateRangePicker


class RepoFooter(FooterBase):
    """Footer that shows repository path alongside key bindings."""

    def __init__(self, repo_path: Path, *args, **kwargs):
        self.repo_path = repo_path
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        # Yield repo label FIRST so it appears leftmost
        yield Label(f"Repository: {self.repo_path}", id="footer-repo-label", classes="footer-repo-label")
        yield from super().compose()

from git_cleaner.logo import CLEAN_LOGO
from git_cleaner.config import (
    get_protected_patterns,
    get_blacklist_patterns,
    load_theme,
    matches_any,
    save_theme,
)
from git_cleaner.git_ops import (
    BranchInfo,
    list_branches,
    delete_branches,
    delete_remote_branches,
    get_repo_root,
    get_git_dir_size,
    get_object_stats,
    run_gc,
    repack_objects,
    prune_remote,
    expire_reflog,
)

GIT_CLEANER_CSS = """
Screen {
    align: center top;
}

Header {
    background: $primary 20%;
}

Footer {
    background: $primary 10%;
}

/* === Main content vertical centering === */
#main-content {
    align: center top;
    height: 1fr;
    width: 100%;
    overflow-y: auto;
}

/* === Title === */
#title {
    text-style: bold;
    text-align: center;
    padding: 0 1;
    height: 3;
    color: $primary;
}

#title-banner {
    height: auto;
    padding: 0 2;
    margin: 0 2;
    border: solid $primary 30%;
    text-align: center;
    overflow-x: auto;
    max-width: 100%;
}

#ascii-logo {
    text-style: bold;
    color: #10B981;
    height: 4;
    width: 100%;
    margin: 0;
    padding: 0;
    text-align: center;
    overflow-x: auto;
}

#repo-label {
    padding: 0 1 1 1;
    color: $text-muted;
    text-align: center;
    height: 1;
}

/* === Date range picker labels === */
#lbl-from, #lbl-until {
    color: $text-muted;
    width: 6;
    text-align: right;
    padding: 0 1 0 0;
}

/* === Centering wrapper === */
.center-row {
    align: center middle;
    height: auto;
    width: 100%;
}

#date-picker {
    margin: 1 0 0 0;
}

/* === Load button === */
#load-btn {
    width: 24;
}

/* === Button row spacing === */
.button-row {
    margin: 1 0 0 0;
}

/* Error message */
#error-msg {
    color: $error;
    height: 1;
    text-align: center;
}

/* === Branch list screen === */
#range-label {
    padding: 0 1;
    color: $text-muted;
    text-align: center;
    height: 1;
}

#action-row {
    height: auto;
    margin: 0 0 0 1;
    align: left middle;
    width: 100%;
}

#toggle-remote {
    width: 18;
    min-width: 18;
}

#branch-table {
    height: 1fr;
    margin: 0 1;
    width: 100%;
}

DataTable {
    height: 1fr;
}

DataTable > .datatable--header {
    text-style: bold;
    background: $primary 20%;
}

#status-bar {
    height: 1;
    padding: 0 1;
    color: $text-muted;
}

/* === Confirmation dialog === */
#dialog {
    width: auto;
    min-width: 40;
    max-width: 70;
    height: auto;
    border: solid $primary;
    padding: 1 2;
    background: $surface;
    align: center middle;
}

#dialog > Label {
    text-style: bold;
    padding: 0 0 1 0;
}

#dialog Horizontal {
    height: auto;
    margin: 1 0;
    align: center middle;
}

#dialog Button {
    margin: 0 1;
    min-width: 10;
}

/* === Maintenance screen === */

.section-title {
    text-style: bold;
    padding: 0 0 1 0;
    color: $text;
}

#health-stats {
    height: auto;
    margin: 0 2;
    padding: 0 1 0 2;
    border: solid $primary 30%;
}

#health-stats-header {
    height: auto;
    align: center middle;
}

#health-stats-title {
    text-style: bold;
}

#health-stats-spacer {
    width: 1fr;
}

#refresh-health {
    min-width: 3;
}

#health-stats .health-stat {
    padding: 0 1;
    height: 1;
}

#health-status-bar {
    height: auto;
    padding: 0 1;
    margin: 0 0 0 0;
}

#health-status-label {
    text-style: bold;
    padding: 0;
}

#health-status-badge {
    padding: 0 0 0 1;
}

#health-status-badge.good {
    color: $success;
}

#health-status-badge.fair {
    color: $warning;
}

#health-status-badge.poor {
    color: $error;
}

#health-status-divider {
    color: $text-muted;
    padding: 0 1;
}

#health-recommendations {
    height: auto;
    margin: 0 0 0 0;
}

#health-recommendations .reco-item {
    height: 1;
    padding: 0 1;
    color: $text-muted;
}

#health-recommendations .reco-item.needs-attention {
    color: $warning;
}

#health-recommendations .reco-item.all-good {
    color: $text-muted;
    text-style: italic;
}

#tasks-section {
    height: auto;
    margin: 1 2;
}

.task-row {
    height: auto;
    align: center middle;
    margin: 0 0 1 0;
    overflow-x: auto;
}

.task-button {
    margin: 0 1 0 0;
    min-width: 16;
}

/* === Status bar (always visible above task buttons) === */
#task-status-bar {
    height: auto;
    margin: 0 2 1 2;
    padding: 0 1;
    border: solid $primary 30%;
    align: center middle;
}

#task-spinner {
    display: none;
    width: 3;
    height: 1;
}

#task-status {
    height: 1;
    padding: 0 0 0 1;
}

/* === Command output log === */
#task-output {
    height: 6;
    max-height: 30;
    margin: 0 2;
    padding: 1;
    border: solid $surface;
    background: $surface 50%;
}

#maintenance-actions {
    height: auto;
    margin: 1 0;
    align: center middle;
}

/* === Task help legend === */

#help-legend {
    height: auto;
    margin: 0 2;
    padding: 1 2;
    border: dashed $surface;
    overflow-x: auto;
}

#help-legend Label {
    padding: 0 1;
    height: 1;
    color: $text-muted;
}

#repo-label-bottom {
    padding: 1 2;
    color: $text-muted;
    text-align: left;
    height: 1;
}

#bottom-bar {
    height: auto;
    margin: 1 2 0 2;
    align: left middle;
    padding: 0 1;
}

#bottom-bar Button {
    margin-left: 2;
}

.footer-repo-label {
    color: $text-muted;
    padding: 0 1;
    height: 1;
    text-align: left;
}
"""


class CalendarContent(Vertical):
    """Panel with a DateRangePicker and navigation buttons."""

    def __init__(self, screen: Screen) -> None:
        super().__init__(id="main-content")
        self._screen = screen

    @property
    def repo_path(self) -> Path:
        return self._screen.repo_path

    def compose(self) -> ComposeResult:
        with Vertical(id="title-banner"):
            yield Static(CLEAN_LOGO, id="ascii-logo")
            yield Label(f"Repository: {self.repo_path}", id="repo-label")

        with Horizontal(classes="center-row"):
            yield DateRangePicker(id="date-picker")

        with Horizontal(classes="center-row button-row"):
            yield Button("Load Branches", variant="primary", id="load-btn")
            yield Button("Maintenance", variant="default", id="maintenance-btn")

        yield Static(id="error-msg")
        with Horizontal(id="bottom-bar"):
            yield Label(f"Repository: {self.repo_path}", id="repo-label-bottom")

    async def _on_mount(self) -> None:
        """Inject From/Until labels into the DateRangePicker input row."""
        picker = self.query_one(DateRangePicker)
        control = picker.query_one("#input-control")
        await control.mount(
            Label("From:", id="lbl-from"),
            before=picker.query_one("#start-date-input"),
        )
        await control.mount(
            Label("Until:", id="lbl-until"),
            before=picker.query_one("#stop-date-input"),
        )

    @on(DateRangePicker.Changed)
    def _collapse_after_range_set(self, event: DateRangePicker.Changed) -> None:
        """Collapse the picker overlay once both dates are selected."""
        if event.start and event.end:
            self.query_one(DateRangePicker).expanded = False

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "load-btn":
            await self._load_branches()
        elif btn_id == "maintenance-btn":
            await self.app.push_screen(MaintenanceScreen(self.repo_path))

    async def _load_branches(self) -> None:
        error_msg = self.query_one("#error-msg", Static)
        picker = self.query_one("#date-picker", DateRangePicker)

        if not picker.start_date or not picker.end_date:
            error_msg.update("Please select both From and Until dates.")
            return

        if picker.start_date > picker.end_date:
            error_msg.update("'From' date must be before 'Until' date.")
            return

        try:
            get_repo_root(self.repo_path)
        except RuntimeError as e:
            error_msg.update(str(e))
            return

        error_msg.update("")
        await self.app.push_screen(
            BranchListScreen(
                repo_path=self.repo_path,
                since=picker.start_date.py_date(),
                until=picker.end_date.py_date(),
            )
        )


class CalendarScreen(Screen):
    """Screen with a date range picker."""

    def __init__(self, repo_path: Path) -> None:
        super().__init__()
        self.title = "Git Cleaner"
        self.repo_path = repo_path

    def compose(self) -> ComposeResult:
        yield Header()
        yield CalendarContent(self)
        yield RepoFooter(self.repo_path)


# ─── Task key → label mapping for maintenance buttons ──────────────────────

_TASK_MAP: dict[str, tuple[str, str]] = {
    "gc-btn": ("gc", "Git GC"),
    "gc-agg-btn": ("gc-agg", "GC Aggressive"),
    "repack-btn": ("repack", "Repack"),
    "prune-btn": ("prune", "Prune Remote"),
    "reflog-btn": ("reflog", "Expire Reflog"),
    "all-btn": ("all", "Run All"),
}


class MaintenanceScreen(Screen):
    """Screen for git repository health display and maintenance tasks."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("r", "refresh_health", "Refresh health"),
    ]

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        self._task_running = False
        super().__init__()
        self.title = "Git Cleaner"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-content"):
            with Vertical(id="title-banner"):
                yield Static(CLEAN_LOGO, id="ascii-logo")
                yield Label(f"Repository: {self.repo_path}", id="repo-label")

            with Vertical(id="health-stats"):
                with Horizontal(id="health-stats-header"):
                    yield Label("Repository Health", id="health-stats-title")
                    yield Label("", id="health-stats-spacer")
                    yield Button("⟳", id="refresh-health", variant="default", tooltip="Refresh health stats")
                with Horizontal(id="health-status-bar"):
                    yield Label("Status:", id="health-status-label")
                    yield Label("—", id="health-status-badge")
                    yield Label("|", id="health-status-divider")
                    yield Label("No recommendations", id="health-status-reco")
                yield Label("", id="stat-git-size", classes="health-stat")
                yield Label("", id="stat-loose", classes="health-stat")
                yield Label("", id="stat-packed", classes="health-stat")
                yield Label("", id="stat-garbage", classes="health-stat")
                yield Label("", id="stat-prune", classes="health-stat")
                with Vertical(id="health-recommendations"):
                    yield Label("", id="reco-0", classes="reco-item")
                    yield Label("", id="reco-1", classes="reco-item")
                    yield Label("", id="reco-2", classes="reco-item")

            # ── Status bar (always visible above buttons) ──────────────
            with Horizontal(id="task-status-bar"):
                yield LoadingIndicator(id="task-spinner")
                yield Label("Idle — click a task below to run", id="task-status")

            with Vertical(id="tasks-section"):
                yield Label("Maintenance Tasks", classes="section-title")
                with Vertical(id="task-buttons"):
                    with Horizontal(classes="task-row"):
                        yield Button(
                            "Git GC",
                            id="gc-btn",
                            classes="task-button",
                            variant="primary",
                            tooltip="git gc — Compress revisions, remove loose objects. Standard housekeeping.",
                        )
                        yield Button(
                            "GC Aggressive",
                            id="gc-agg-btn",
                            classes="task-button",
                            variant="warning",
                            tooltip="git gc --aggressive — Deep optimization. Slower but thorough; run quarterly.",
                        )
                        yield Button(
                            "Repack",
                            id="repack-btn",
                            classes="task-button",
                            variant="primary",
                            tooltip="git repack -Ad — Reorganize pack files for better delta compression.",
                        )
                    with Horizontal(classes="task-row"):
                        yield Button(
                            "Prune Remote",
                            id="prune-btn",
                            classes="task-button",
                            variant="default",
                            tooltip="git remote prune origin — Remove stale remote-tracking refs for deleted upstream branches.",
                        )
                        yield Button(
                            "Expire Reflog",
                            id="reflog-btn",
                            classes="task-button",
                            variant="default",
                            tooltip="git reflog expire --expire=90.days.ago — Trim old reflog entries to shrink .git.",
                        )
                        yield Button(
                            "Run All",
                            id="all-btn",
                            classes="task-button",
                            variant="error",
                            tooltip="Run GC, Repack, Prune Remote, and Expire Reflog in sequence.",
                        )

            yield RichLog(id="task-output", highlight=True, markup=True, max_lines=100)

            # Collapsible help legend
            with Vertical(id="help-legend"):
                yield Label("What each operation does:", classes="section-title")
                yield Label("• Git GC — Standard housekeeping: compresses revisions and removes unreachable objects")
                yield Label("• GC Aggressive — Deep re-delta: takes longer but finds better compression")
                yield Label("• Repack — Restructures pack files without full GC overhead")
                yield Label("• Prune Remote — Cleans up local tracking refs for branches already deleted upstream")
                yield Label("• Expire Reflog — Drops reflog entries older than 90 days to free disk space")
                yield Label("• Run All — Runs all the above tasks in order (takes the longest)")

            # Repository path inline with bottom buttons
            with Horizontal(id="bottom-bar"):
                yield Label(f"Repository: {self.repo_path}", id="repo-label-bottom")
                yield Button("Back", id="back-btn", variant="default")

        yield RepoFooter(self.repo_path)

    def on_mount(self) -> None:
        self._update_health()

    # ── Health stats ────────────────────────────────────────────────────

    def _assess_health(self, stats: dict[str, str]) -> tuple[str, str, list[str]]:
        """Analyse stats and return (badge_text, badge_class, recommendations)."""
        try:
            count = int(stats.get("count", "0"))
            garbage = int(stats.get("garbage", "0"))
            pp = int(stats.get("prune-packable", "0"))
        except ValueError:
            return "Unknown", "fair", []

        issues: list[str] = []

        if count > 200:
            issues.append(f"High loose object count ({count}) — run Git GC to pack them")
        elif count > 50:
            issues.append(f"{count} loose objects — run Git GC to pack them")

        if garbage > 0:
            items = "items" if garbage > 1 else "item"
            issues.append(f"{garbage} garbage {items} — run Git GC to clean up")

        if pp > 50:
            issues.append(f"{pp} prune-packable objects — run Repack for better delta compression")
        elif pp > 0:
            issues.append(f"{pp} prune-packable objects — run Repack")

        if not issues:
            return "Good", "good", []

        if len(issues) <= 1:
            return "Fair", "fair", issues

        return "Needs Attention", "poor", issues

    def _update_health(self) -> None:
        try:
            git_size = get_git_dir_size(self.repo_path)
            stats = get_object_stats(self.repo_path)
        except RuntimeError as e:
            self._show_done(f"Error: {e}", error=True)
            return

        self.query_one("#stat-git-size", Label).update(f".git size: {git_size}")

        count = stats.get("count", "0")
        size = stats.get("size", "0")
        in_pack = stats.get("in-pack", "0")
        packs = stats.get("packs", "0")
        size_pack = stats.get("size-pack", "0")
        garbage = stats.get("garbage", "0")
        size_garbage = stats.get("size-garbage", "0")
        prune_packable = stats.get("prune-packable", "0")

        try:
            sz = int(size)
            loose_extra = f" ({sz} KiB)" if sz else ""
        except ValueError:
            loose_extra = ""
        self.query_one("#stat-loose", Label).update(
            f"Loose objects: {count}{loose_extra}"
        )

        try:
            sp = int(size_pack)
            pk = int(packs)
            packed_extra = f" ({sp} KiB in {pk} packs)" if pk else ""
        except ValueError:
            packed_extra = ""
        self.query_one("#stat-packed", Label).update(
            f"Packed objects: {in_pack}{packed_extra}"
        )

        try:
            sg = int(size_garbage)
            garbage_extra = f" ({sg} KiB)" if sg else ""
        except ValueError:
            garbage_extra = ""
        self.query_one("#stat-garbage", Label).update(
            f"Garbage objects: {garbage}{garbage_extra}"
        )

        self.query_one("#stat-prune", Label).update(
            f"Prune-packable: {prune_packable}"
        )

        # ── Health assessment ────────────────────────────────────────
        badge, css_class, recommendations = self._assess_health(stats)

        badge_widget = self.query_one("#health-status-badge", Label)
        badge_widget.update(badge)
        badge_widget.remove_class("good", "fair", "poor")
        badge_widget.add_class(css_class)

        # Show the most actionable recommendation inline
        reco_summary = self.query_one("#health-status-reco", Label)
        if recommendations:
            reco_summary.update(recommendations[0])
        else:
            reco_summary.update("Repo is healthy")

        # Fill the recommendation detail lines
        for i in range(3):
            item = self.query_one(f"#reco-{i}", Label)
            if i < len(recommendations):
                item.update(f"• {recommendations[i]}")
                item.remove_class("all-good", "needs-attention")
                item.add_class("needs-attention")
            else:
                item.remove_class("needs-attention", "all-good")
                if i == 0 and not recommendations:
                    item.update("✓ No maintenance needed")
                    item.add_class("all-good")
                else:
                    item.update("")

    async def _refresh_health_async(self) -> None:
        """Refresh health stats with visual feedback."""
        # Show immediate feedback
        self.query_one("#task-spinner", LoadingIndicator).display = True
        self.query_one("#task-status", Label).update("Refreshing health…")
        
        try:
            # Run in thread to avoid blocking UI
            await asyncio.to_thread(self._update_health)
            self.query_one("#task-status", Label).update("Health refreshed")
        except Exception as e:
            self.query_one("#task-status", Label).update(f"Error: {e}")
        finally:
            self.query_one("#task-spinner", LoadingIndicator).display = False

    def action_refresh_health(self) -> None:
        self._update_health()

    # ── Task execution ──────────────────────────────────────────────────

    # ── Output helpers ──────────────────────────────────────────────────

    def _show_running(self, label: str) -> None:
        self.query_one("#task-spinner", LoadingIndicator).display = True
        self.query_one("#task-status", Label).update(f"Running {label}…")
        self.notify(f"▶ Running {label}", timeout=3)
        rl = self.query_one("#task-output", RichLog)
        rl.clear()
        rl.write(f"[bold yellow]▶ Running {label}…[/]\n")

    def _show_done(self, msg: str, error: bool = False) -> None:
        self.query_one("#task-spinner", LoadingIndicator).display = False
        status = self.query_one("#task-status", Label)
        status.update(msg)
        if error:
            status.styles.color = "#FF4444"
        else:
            # Remove any previously set color so theme default applies
            status.styles.color = ""
        icon = "✗" if error else "✓"
        self.notify(f"{icon} {msg}", severity="error" if error else "information", timeout=5)
        rl = self.query_one("#task-output", RichLog)
        rl.write(f"[{'bold red' if error else 'bold green'}]{icon} {msg}[/]")

    def _on_output(self, line: str) -> None:
        """Thread‑safe output callback — forward to RichLog on the event loop."""
        self.app.call_from_thread(self._write_output, line)

    def _write_output(self, line: str) -> None:
        self.query_one("#task-output", RichLog).write(line)

    def _set_buttons_enabled(self, enabled: bool) -> None:
        for btn_id in _TASK_MAP:
            try:
                self.query_one(f"#{btn_id}", Button).disabled = not enabled
            except Exception:
                pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        # Show immediate feedback synchronously
        try:
            self.query_one("#task-spinner", LoadingIndicator).display = True
            self.query_one("#task-status", Label).update(f"Running {btn_id}…")
        except Exception:
            pass

        if btn_id == "refresh-health":
            await self._refresh_health_async()
        elif btn_id == "back-btn":
            self.app.pop_screen()
        elif btn_id in _TASK_MAP:
            if self._task_running:
                return
            task_key, task_label = _TASK_MAP[btn_id]
            await self._run_tasks(task_key, task_label)

    async def _run_tasks(self, task_key: str, task_label: str) -> None:
        self._task_running = True
        self._set_buttons_enabled(False)
        try:
            self._show_running(task_label)

            # Run in thread — if this hangs, asyncio.to_thread is the culprit
            if task_key == "all":
                success, msg = await asyncio.to_thread(
                    self._run_all_tasks, self._on_output
                )
            else:
                success, msg = await asyncio.to_thread(
                    self._execute_single, task_key, self._on_output
                )
            self._show_done(msg, error=not success)
        except Exception as e:
            self._show_done(f"Error: {e}", error=True)
        finally:
            self._task_running = False
            self._set_buttons_enabled(True)
            self._update_health()

    def _execute_single(
        self, task_key: str, on_output
    ) -> tuple[bool, str]:
        dispatcher = {
            "gc": lambda: run_gc(self.repo_path, on_output=on_output),
            "gc-agg": lambda: run_gc(
                self.repo_path, aggressive=True, on_output=on_output
            ),
            "repack": lambda: repack_objects(self.repo_path, on_output=on_output),
            "prune": lambda: prune_remote(self.repo_path, on_output=on_output),
            "reflog": lambda: expire_reflog(self.repo_path, on_output=on_output),
        }
        fn = dispatcher.get(task_key)
        if fn is None:
            return False, f"Unknown task: {task_key}"
        return fn()

    def _run_all_tasks(self, on_output) -> tuple[bool, str]:
        subtasks = [
            ("GC", lambda p: run_gc(p, on_output=on_output)),
            ("Repack", lambda p: repack_objects(p, on_output=on_output)),
            ("Prune", lambda p: prune_remote(p, on_output=on_output)),
            ("Reflog", lambda p: expire_reflog(p, on_output=on_output)),
        ]
        results: list[str] = []
        all_ok = True
        for name, fn in subtasks:
            on_output(f"\n── {name} ──\n")
            success, msg = fn(self.repo_path)
            results.append(f"{'✓' if success else '✗'} {name}: {msg}")
            if not success:
                all_ok = False
        return all_ok, "\n".join(results)

    def action_go_back(self) -> None:
        self.app.pop_screen()


class ConfirmationDialog(ModalScreen[bool]):
    """Modal dialog to confirm branch deletion."""

    def __init__(self, branches: list[str], delete_remote: bool = False) -> None:
        self.branches = branches
        self.delete_remote = delete_remote
        super().__init__()

    def compose(self) -> ComposeResult:
        branch_list = "\n".join(f"  • {b}" for b in self.branches)
        scope = " locally and on remote" if self.delete_remote else ""
        yield Vertical(
            Label(f"Delete {len(self.branches)} branch(es){scope}?"),
            Static(branch_list),
            Horizontal(
                Button("Cancel", variant="default", id="cancel"),
                Button("Delete", variant="error", id="confirm"),
            ),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


class BranchListScreen(Screen):
    """Second screen: browse and select branches, then delete."""

    BINDINGS = [
        Binding("space", "toggle_row", "Toggle selection"),
        Binding("a", "select_all", "Select all"),
        Binding("d", "delete_selected", "Delete selected"),
        Binding("p", "toggle_protected", "Toggle protected visibility"),
        Binding("b", "toggle_blacklisted", "Toggle blacklisted visibility"),
        Binding("r", "toggle_remote", "Toggle remote deletion"),
        Binding("escape", "go_back", "Back"),
        Binding("ctrl+r", "refresh", "Refresh"),
    ]

    def __init__(
        self,
        repo_path: Path,
        since: date | None = None,
        until: date | None = None,
    ) -> None:
        self.repo_path = repo_path
        self.since = since
        self.until = until
        self.show_protected = False
        self.show_blacklisted = False
        self.delete_remote = False
        self.branches: list[BranchInfo] = []
        self.selected: set[str] = set()
        super().__init__()
        self.title = "Git Cleaner"

    def compose(self) -> ComposeResult:
        yield Header()
        range_label = (
            f"From: {self.since or 'any'}  To: {self.until or 'any'}"
        )
        with Vertical(id="title-banner"):
            yield Static(CLEAN_LOGO, id="ascii-logo")
        yield DataTable(id="branch-table")
        with Horizontal(id="action-row"):
            mode_label = "Remote: ON" if self.delete_remote else "Remote: OFF"
            remote_variant = "primary" if self.delete_remote else "default"
            yield Button(mode_label, id="toggle-remote", variant=remote_variant)
        yield Static(id="status-bar")
        with Horizontal(id="bottom-bar"):
            yield Label(f"Repository: {self.repo_path}", id="repo-label-bottom")
        yield RepoFooter(self.repo_path)

    def on_mount(self) -> None:
        table = self.query_one("#branch-table", DataTable)
        table.add_columns("✓", "Branch", "Last Commit", "Status")
        self._load_branches()

    def _load_branches(self) -> None:
        since_dt = (
            datetime(
                self.since.year,
                self.since.month,
                self.since.day,
                tzinfo=timezone.utc,
            )
            if self.since
            else None
        )
        until_dt = (
            datetime(
                self.until.year,
                self.until.month,
                self.until.day,
                23,
                59,
                59,
                tzinfo=timezone.utc,
            )
            if self.until
            else None
        )

        all_branches = list_branches(
            self.repo_path, since=since_dt, until=until_dt
        )

        protected_patterns = get_protected_patterns(self.repo_path)
        blacklist_patterns = get_blacklist_patterns(self.repo_path)

        for b in all_branches:
            if b.is_current or matches_any(b.name, protected_patterns):
                b.is_protected = True
            if matches_any(b.name, blacklist_patterns):
                b.is_blacklisted = True

        self.branches = all_branches
        self._refresh_table()

    def _refresh_table(self) -> None:
        table = self.query_one("#branch-table", DataTable)
        table.clear()

        for b in self.branches:
            if not self.show_protected and b.is_protected:
                continue
            if not self.show_blacklisted and b.is_blacklisted:
                continue

            checked = "✓" if b.name in self.selected else " "
            status = ""
            if b.is_protected:
                status = "🔒 protected"
            elif b.is_blacklisted:
                status = "⛔ blacklisted"
            elif b.is_current:
                status = "← current"

            date_str = b.commit_date.strftime("%Y-%m-%d")
            table.add_row(checked, b.name, date_str, status)

        self._update_status()

    def _update_status(self) -> None:
        total = len(self.branches)
        n_protected = sum(1 for b in self.branches if b.is_protected)
        n_blacklisted = sum(1 for b in self.branches if b.is_blacklisted)
        n_selected = len(self.selected)
        status = self.query_one("#status-bar", Static)
        status.update(
            f"Total: {total} | Selected: {n_selected} | "
            f"Protected: {n_protected} | Blacklisted: {n_blacklisted} | "
            f"Remote: {'ON' if self.delete_remote else 'OFF'} | "
            f"\\[P]rotected: {'show' if self.show_protected else 'hide'} | "
            f"\\[B]lacklisted: {'show' if self.show_blacklisted else 'hide'}"
        )

    def action_toggle_row(self) -> None:
        table = self.query_one("#branch-table", DataTable)
        row = table.cursor_row
        if row is None:
            return
        row_data = table.get_row_at(row)
        if not row_data:
            return
        name = str(row_data[1])
        branch = next(
            (b for b in self.branches if b.name == name), None
        )
        if branch and (branch.is_protected or branch.is_blacklisted):
            return
        if name in self.selected:
            self.selected.discard(name)
        else:
            self.selected.add(name)
        self._refresh_table()

    def action_select_all(self) -> None:
        selectable = {
            b.name for b in self.branches
            if not b.is_protected and not b.is_blacklisted
        }
        if self.selected & selectable:
            # Some selectable branches are selected → deselect all selectable
            self.selected -= selectable
        else:
            # None selected → select all selectable
            self.selected |= selectable
        self._refresh_table()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "toggle-remote":
            self._toggle_remote()

    def action_toggle_remote(self) -> None:
        self._toggle_remote()

    def _toggle_remote(self) -> None:
        self.delete_remote = not self.delete_remote
        btn = self.query_one("#toggle-remote", Button)
        btn.label = "Remote: ON" if self.delete_remote else "Remote: OFF"
        btn.variant = "primary" if self.delete_remote else "default"
        self._refresh_table()

    def action_delete_selected(self) -> None:
        if not self.selected:
            return

        def handle_confirmation(confirmed: bool) -> None:
            if confirmed:
                to_delete = list(self.selected)
                failed_local = delete_branches(self.repo_path, to_delete)
                failed_remote: list[str] = []
                if self.delete_remote:
                    # Try remote delete only for locally-successful branches
                    remote_targets = [n for n in to_delete if n not in failed_local]
                    if remote_targets:
                        failed_remote = delete_remote_branches(
                            self.repo_path, remote_targets
                        )
                all_failed = list(set(failed_local + failed_remote))
                if all_failed:
                    self.query_one("#status-bar", Static).update(
                        f"Failed: {', '.join(all_failed)}"
                    )
                else:
                    parts = [f"Deleted {len(to_delete)} branch(es)"]
                    if self.delete_remote:
                        parts.append("(local + remote)")
                    self.query_one("#status-bar", Static).update(
                        " ".join(parts)
                    )
                self.selected.clear()
                self._load_branches()

        self.app.push_screen(
            ConfirmationDialog(
                list(self.selected), delete_remote=self.delete_remote
            ),
            handle_confirmation,
        )

    def action_toggle_protected(self) -> None:
        self.show_protected = not self.show_protected
        self._refresh_table()

    def action_toggle_blacklisted(self) -> None:
        self.show_blacklisted = not self.show_blacklisted
        self._refresh_table()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self.selected.clear()
        self._load_branches()


class GitCleanerApp(App):
    """Main TUI application for git branch cleaning."""

    CSS = GIT_CLEANER_CSS

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        super().__init__()
        # Load persisted theme before mount so it applies immediately
        self.theme = load_theme()

    def on_mount(self) -> None:
        self.push_screen(CalendarScreen(self.repo_path))

    def watch_theme(self, old: str, new: str) -> None:
        """Persist theme whenever it changes (e.g. via Ctrl+T toggle)."""
        save_theme(new)
