import asyncio
import re
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

import whenever

from textual import on
from textual.events import Key
from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header,
    Footer,
    Button,
    Input,
    Label,
    Select,
    Static,
    Tree,
    DataTable,
    ListView,
    ListItem,
    LoadingIndicator,
    RichLog,
    TabbedContent,
    TabPane,
)
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual_timepiece.pickers import DateRangePicker


class RepoFooter(Footer):
    """Footer that shows repository path alongside key bindings."""

    def __init__(self, repo_path: Path, *args, **kwargs) -> None:
        self.repo_path = repo_path
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield Label(f"Repository: {self.repo_path}", id="footer-repo-label", classes="footer-repo-label")
        yield from super().compose()


from git_cleaner.config import (
    get_protected_patterns,
    get_blacklist_patterns,
    add_bookmark,
    load_bookmarks,
    load_theme,
    matches_any,
    remove_bookmark,
    save_theme,
)
from git_cleaner.git_ops import (
    BranchInfo,
    StashInfo,
    list_branches,
    list_stashes,
    delete_branches,
    delete_remote_branches,
    get_branch_details,
    get_repo_root,
    get_git_dir_size,
    get_object_stats,
    restore_branch,
    drop_stash,
    apply_stash,
    pop_stash,
    run_gc,
    repack_objects,
    prune_remote,
    expire_reflog,
    get_merge_base,
    get_diff_stat,
    get_shortstat,
    get_commits_symmetric,
    list_worktrees,
    add_worktree,
    remove_worktree,
    prune_worktrees,
    WorktreeInfo,
    get_commit_log,
    get_author_stats,
    get_large_commits,
    PRInfo,
    list_open_prs,
    _detect_provider,
    _get_api_token,
    get_stale_branches_across_repos,
    StaleBranchInfo,
)


def _age_from(dt: datetime) -> str:
    """Return a human-friendly age string from a datetime."""
    delta = datetime.now(timezone.utc) - dt
    if delta.days > 365:
        years = delta.days // 365
        return f"{years}y ago"
    if delta.days > 30:
        months = delta.days // 30
        return f"{months}mo ago"
    if delta.days > 0:
        return f"{delta.days}d ago"
    if delta.seconds >= 3600:
        return f"{delta.seconds // 3600}h ago"
    if delta.seconds >= 60:
        return f"{delta.seconds // 60}m ago"
    return "now"


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

/* === Tab styling === */
ContentTabs {
    background: $surface 50%;
    height: 1;
}

Tab {
    width: auto;
    height: 1;
    padding: 0 2;
    text-align: center;
    color: $text-muted;
    text-style: bold;
    content-align: center middle;
}

Tab:hover {
    color: $text;
    background: $boost;
}

Tab.-active {
    color: $text;
    background: $primary 20%;
    text-style: bold;
}

Tab:disabled {
    color: $text-muted 30%;
}

/* === Date range picker labels === */
#lbl-from, #lbl-until {
    color: $text-muted;
    width: 6;
    text-align: right;
    padding: 0 1 0 0;
}

/* === Date range picker === */
DateRangePicker {
    max-height: 8;
}

/* === Date picker + Load button row === */
#date-btn-row {
    height: auto;
    align: center middle;
    margin: 1 1 1 1;
    overflow-x: auto;
}

/* === Compact buttons (all except DateRangePicker internals) === */
#load-btn, .preset-btn, #toggle-remote, #toggle-dry-run,
#export-csv, #export-json,
.task-button, #refresh-health,
#stash-drop, #stash-apply, #stash-pop, #stash-refresh,
#cancel, #confirm,
#repo-add, #repo-remove, #repo-close {
    min-height: 1;
    padding: 0;
    border: none;
}

/* Date row buttons match DateRangePicker height */
#date-btn-row > #load-btn {
    margin: 0 0 0 2;
    height: 3;
    min-height: 3;
}

.preset-btn {
    margin: 0 0 0 1;
    min-width: 5;
    height: 3;
    min-height: 3;
}

/* === Filter row: search + author + age === */
#filter-row {
    height: auto;
    margin: 0 1 1 1;
    align: left middle;
}

#search-input {
    width: 1fr;
    min-width: 12;
}

#author-select {
    width: 20;
    min-width: 12;
    margin: 0 0 0 1;
}

#age-select {
    width: 16;
    min-width: 12;
    margin: 0 0 0 1;
}

/* === Error / status messages === */
#status-bar {
    height: 1;
    padding: 0 2;
    margin: 0 1;
    color: $text-muted;
}

/* === Action row (remote toggle + export) === */
#action-row {
    height: auto;
    margin: 0 1;
    align: left middle;
    width: 100%;
    overflow-x: auto;
}

#action-spacer {
    width: 1fr;
    height: 1;
}

#toggle-remote {
    width: 18;
    min-width: 18;
}

#toggle-dry-run {
    width: 18;
    min-width: 18;
    margin: 0 0 0 1;
}

#export-csv, #export-json {
    margin: 0 0 0 1;
}

/* === Branch tree === */
#branches-pane > Vertical, #stash-pane > Vertical {
    height: 1fr;
}

#branch-table {
    height: 1fr;
    margin: 0 1;
    width: 100%;
}

#details-pane {
    height: auto;
    max-height: 6;
    margin: 0 1 1 1;
    padding: 0 1;
    border: solid $primary 20%;
    background: $surface 50%;
    overflow-y: auto;
}

Tree {
    height: 1fr;
}

Tree:focus {
    border: none;
}

/* === Tabbed content pane === */
#branches-pane, #maintenance-pane, #stash-pane {
    padding: 0 0;
    height: 1fr;
}

/* === Maintenance pane === */
.section-title {
    text-style: bold;
    padding: 0;
    color: $text;
}

#health-stats {
    height: auto;
    margin: 0 1 1 1;
    padding: 0 1;
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
    color: $text-muted;
}

#health-status-bar {
    height: auto;
    padding: 0 1;
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

#health-status-reco {
    padding: 0;
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
    margin: 0 1 1 1;
}

.task-row {
    height: auto;
    align: center middle;
    margin: 0 0 1 0;
    overflow-x: auto;
}

.task-button {
    margin: 0 1;
    min-width: 14;
}

/* === Status bar (always visible above task buttons) === */
#task-status-bar {
    height: auto;
    margin: 0 1 1 1;
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
    height: 4;
    max-height: 20;
    margin: 0 1 1 1;
    padding: 0 1;
    border: solid $surface;
    background: $surface 50%;
}

/* === Task help legend === */
#help-legend {
    height: auto;
    margin: 0 1 1 1;
    padding: 0 1;
    border: dashed $surface;
    overflow-x: auto;
}

#help-legend Label {
    padding: 0 1;
    height: 1;
    color: $text-muted;
}

/* === Confirmation dialog === */
#dialog {
    width: auto;
    min-width: 30;
    max-width: 60;
    height: auto;
    border: solid $primary;
    padding: 0 1;
    background: $surface;
    align: center middle;
}

#dialog > Label {
    text-style: bold;
    padding: 0;
}

#dialog Horizontal {
    height: auto;
    align: center middle;
}

#dialog Button {
    margin: 0 1;
    min-width: 8;
}

/* === Stash browser === */
#stash-table {
    height: 1fr;
    margin: 1 1 1 1;
}

#stash-actions {
    height: auto;
    margin: 1 1 1 1;
    align: center middle;
    overflow-x: auto;
}

#stash-actions Button {
    margin: 0 1;
    min-width: 10;
}

#stash-status {
    height: 1;
    margin: 0 0 1 0;
    padding: 0 2;
    color: $text-muted;
}

/* === PR/MR browser === */
#pr-table {
    height: 1fr;
    margin: 1 1 1 1;
}

#pr-actions {
    height: auto;
    margin: 1 1 1 1;
    align: center middle;
    overflow-x: auto;
}

#pr-actions Button {
    margin: 0 1;
    min-width: 10;
}

#pr-actions > #pr-status {
    width: 1fr;
    content-align: right middle;
    padding: 0 2;
    color: $text-muted;
}

/* === Stale branches browser === */
#stale-table {
    height: 1fr;
    margin: 1 1 1 1;
}

#stale-actions {
    height: auto;
    margin: 1 1 1 1;
    align: center middle;
    overflow-x: auto;
}

#stale-actions Button {
    margin: 0 1;
    min-width: 10;
}

#stale-actions > #stale-status {
    width: 1fr;
    content-align: right middle;
    padding: 0 2;
    color: $text-muted;
}

/* === Worktrees browser === */
#wt-table {
    height: 1fr;
    margin: 1 1 1 1;
}

#wt-actions {
    height: auto;
    margin: 1 1 1 1;
    align: center middle;
    overflow-x: auto;
}

#wt-actions Button {
    margin: 0 1;
    min-width: 10;
}

#wt-actions > #wt-status {
    width: 1fr;
    content-align: right middle;
    padding: 0 2;
    color: $text-muted;
}

/* === Commit analysis === */
#commit-select-row {
    height: 3;
    padding: 0 1;
    margin: 1 0 0 0;
}

#commit-log-table, #commit-authors-table, #commit-hotspots-table {
    height: 1fr;
    margin: 0 1 1 1;
}

/* === Compare branches === */
#compare-select-row {
    height: auto;
    padding: 0 1;
    margin: 1 0 0 0;
    align: center middle;
}

#compare-select-row > Select {
    width: 1fr;
    margin: 0 1;
}

#compare-select-row > #compare-run {
    margin: 0 1;
}

#compare-result {
    height: 1fr;
    overflow-y: auto;
    padding: 0 1;
    margin: 1 1 1 1;
}

#compare-actions {
    height: auto;
    margin: 1 1 1 1;
    align: center middle;
    overflow-x: auto;
}

#compare-actions > #compare-summary {
    width: 1fr;
    content-align: right middle;
    padding: 0 2;
    color: $text-muted;
}

/* === Repo switcher dialog === */
#repo-list {
    height: auto;
    max-height: 20;
    margin: 1 0;
    border: solid $primary 30%;
}
"""


# ─── Task key → label mapping for maintenance ─────────────────────────────

_TASK_MAP: dict[str, tuple[str, str]] = {
    "gc-btn": ("gc", "Git GC"),
    "gc-agg-btn": ("gc-agg", "GC Aggressive"),
    "repack-btn": ("repack", "Repack"),
    "prune-btn": ("prune", "Prune Remote"),
    "reflog-btn": ("reflog", "Expire Reflog"),
    "all-btn": ("all", "Run All"),
}


class BranchesContent(Vertical):
    """Branches tab: date picker + search/author filter + branch table."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        self.branches: list[BranchInfo] = []
        self.selected: set[str] = set()
        self.show_protected = False
        self.show_blacklisted = False
        self.delete_remote = False
        self.dry_run = False
        self._undo_stack: list[dict[str, str]] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        with Horizontal(id="date-btn-row"):
            yield DateRangePicker(id="date-picker")
            yield Button("7d", id="preset-7d", classes="preset-btn")
            yield Button("30d", id="preset-30d", classes="preset-btn")
            yield Button("90d", id="preset-90d", classes="preset-btn")
            yield Button("1y", id="preset-1y", classes="preset-btn")
            yield Button("Load Branches", id="load-btn", variant="primary")
        with Horizontal(id="filter-row"):
            yield Input(placeholder="Search branches...", id="search-input", compact=True)
            yield Select([], id="author-select", prompt="All authors", allow_blank=True, compact=True)
            yield Select(
                [("7 days", 7), ("30 days", 30), ("90 days", 90), ("180 days", 180), ("1 year", 365)],
                id="age-select",
                prompt="All ages",
                allow_blank=True,
                compact=True,
            )
        yield Tree("", id="branch-table")
        yield Vertical(Static("Click a branch to see details", id="details-content"), id="details-pane")
        with Horizontal(id="action-row"):
            yield Button("Remote: OFF", id="toggle-remote", variant="warning")
            yield Button("Dry Run: OFF", id="toggle-dry-run", variant="primary")
            yield Static("", id="action-spacer")
            yield Button("Export as CSV", id="export-csv", variant="primary")
            yield Button("Export as JSON", id="export-json", variant="primary")
        yield Static(id="status-bar")

    async def on_mount(self) -> None:
        """Inject From/Until labels into DateRangePicker."""
        picker = self.query_one("#date-picker", DateRangePicker)
        control = picker.query_one("#input-control")
        await control.mount(
            Label("From:", id="lbl-from"),
            before=picker.query_one("#start-date-input"),
        )
        await control.mount(
            Label("Until:", id="lbl-until"),
            before=picker.query_one("#stop-date-input"),
        )

        tree = self.query_one("#branch-table", Tree)
        tree.action_toggle_node = self.toggle_row  # ponytail: hijack space → selection toggle
        tree.root.expand()

    @on(DateRangePicker.Changed)
    def _collapse_picker(self, event: DateRangePicker.Changed) -> None:
        """Collapse the picker overlay once both dates are selected."""
        if event.start and event.end:
            self.query_one(DateRangePicker).expanded = False

    @on(Tree.NodeSelected)
    async def _on_node_selected(self, event: Tree.NodeSelected) -> None:
        """Show branch details when a leaf node is selected."""
        details = self.query_one("#details-content", Static)
        node = event.node
        if node is None or node.data is None:  # group node
            return
        branch_name = str(node.data)
        details.update("[dim]Loading…[/]")
        try:
            info = await asyncio.to_thread(get_branch_details, self.repo_path, branch_name)
            details.update(info)
        except Exception as e:
            details.update(f"[red]Error: {e}[/]")

    @on(Input.Changed)
    def _on_search_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self._refresh_table()

    @on(Select.Changed)
    def _on_filter_changed(self, event: Select.Changed) -> None:
        if event.select.id in ("author-select", "age-select"):
            self._refresh_table()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "load-btn":
            await self._load_branches()
        elif btn_id == "toggle-remote":
            self._toggle_remote()
        elif btn_id == "toggle-dry-run":
            self._toggle_dry_run()
        elif btn_id == "export-csv":
            self._export_csv()
        elif btn_id == "export-json":
            self._export_json()
        elif btn_id and btn_id.startswith("preset-"):
            await self._apply_date_preset(btn_id)

    async def _load_branches(self) -> None:
        picker = self.query_one("#date-picker", DateRangePicker)
        status = self.query_one("#status-bar", Static)

        if not picker.start_date or not picker.end_date:
            status.update("Please select both From and Until dates.")
            return
        if picker.start_date > picker.end_date:
            status.update("'From' date must be before 'Until' date.")
            return

        try:
            get_repo_root(self.repo_path)
        except RuntimeError as e:
            status.update(str(e))
            return

        status.update("")

        since_dt = datetime(
            picker.start_date.year, picker.start_date.month, picker.start_date.day,
            tzinfo=timezone.utc,
        )
        until_dt = datetime(
            picker.end_date.year, picker.end_date.month, picker.end_date.day,
            23, 59, 59, tzinfo=timezone.utc,
        )

        all_branches = list_branches(self.repo_path, since=since_dt, until=until_dt)

        protected_patterns = get_protected_patterns(self.repo_path)
        blacklist_patterns = get_blacklist_patterns(self.repo_path)

        for b in all_branches:
            if b.is_current or matches_any(b.name, protected_patterns):
                b.is_protected = True
            if matches_any(b.name, blacklist_patterns):
                b.is_blacklisted = True

        self.branches = all_branches

        # Populate author dropdown
        authors = sorted({b.author for b in all_branches if b.author})
        select = self.query_one("#author-select", Select)
        select.set_options([(a, a) for a in authors])

        self._refresh_table()

    async def _apply_date_preset(self, btn_id: str) -> None:
        """Set date range from a preset button like preset-7d, preset-30d, preset-1y."""
        suffix = btn_id.removeprefix("preset-")
        if suffix.endswith("d"):
            days = int(suffix.rstrip("d"))
            start = date.today() - timedelta(days=days)
            end = date.today()
        elif suffix == "1y":
            start = date.today() - timedelta(days=365)
            end = date.today()
        else:
            return
        picker = self.query_one("#date-picker", DateRangePicker)
        picker.start_date = whenever.Date(start.year, start.month, start.day)
        picker.end_date = whenever.Date(end.year, end.month, end.day)
        picker.expanded = False
        await self._load_branches()

    @staticmethod
    def _upstream_str(b: BranchInfo) -> str:
        if not b.has_upstream:
            return "—"
        if b.ahead == 0 and b.behind == 0:
            return "="
        parts = []
        if b.ahead > 0:
            parts.append(f"↑{b.ahead}")
        if b.behind > 0:
            parts.append(f"↓{b.behind}")
        return " ".join(parts)

    @staticmethod
    def _get_health_indicator(branch: BranchInfo) -> str:
        """Return health indicator string based on branch status."""
        indicators = []
        if branch.is_current:
            indicators.append("@")
        if branch.ahead and branch.ahead > 0:
            indicators.append(f"+{branch.ahead}")
        if branch.behind and branch.behind > 0:
            indicators.append(f"-{branch.behind}")
        return " ".join(indicators) if indicators else ""

    @staticmethod
    def _get_status_badge(branch: BranchInfo) -> str:
        """Return status badge string based on branch classification."""
        badges = []
        if branch.is_protected:
            badges.append("protected")
        if branch.is_blacklisted:
            badges.append("blacklisted")
        return " ".join(badges) if badges else ""

    def _add_branch_node(self, parent, b: BranchInfo) -> None:
        """Add a branch leaf node to a tree parent."""
        selected = b.name in self.selected
        checked = "✓ " if selected else "  "
        upstream = self._upstream_str(b)
        age = _age_from(b.commit_date)
        age_color = self._get_staleness_color(b.commit_date)
        stale = " [red]! stale[/]" if self._is_stale(b) else ""
        health = self._get_health_indicator(b)
        badge = self._get_status_badge(b)
        name_display = f"{b.name} [dim]{health}[/]" if health else b.name
        if badge:
            name_display = f"{name_display} [yellow]({badge})[/]"
        label = f"{checked}[bold]{name_display}[/]  [{age_color}]{age}[/]  [dim]{upstream}[/]{stale}"
        parent.add(label, data=b.name)

    def _build_tree(self) -> None:
        """Rebuild the branch tree from scratch with current filters."""
        tree = self.query_one("#branch-table", Tree)
        tree.clear()

        groups: dict[str, list[BranchInfo]] = {}
        noprefix: list[BranchInfo] = []

        for b in self._filtered_branches():
            if "/" in b.name:
                prefix = b.name.split("/", 1)[0]
                groups.setdefault(prefix, []).append(b)
            else:
                noprefix.append(b)

        # Branches without prefix
        for b in sorted(noprefix, key=lambda x: x.name):
            self._add_branch_node(tree.root, b)

        # Prefix groups (collapsible)
        for prefix in sorted(groups.keys()):
            group_branches = groups[prefix]
            group_node = tree.root.add(f"{prefix} ({len(group_branches)})", data=None)
            group_node.expand()
            for b in sorted(group_branches, key=lambda x: x.name):
                self._add_branch_node(group_node, b)

    def _refresh_table(self) -> None:
        self._build_tree()
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
            f"Dry Run: {'ON' if self.dry_run else 'OFF'} | "
            f"\\[P]rotected: {'show' if self.show_protected else 'hide'} | "
            f"\\[B]lacklisted: {'show' if self.show_blacklisted else 'hide'}"
        )

    @staticmethod
    def _is_stale(b: BranchInfo) -> bool:
        return (datetime.now(timezone.utc) - b.commit_date).days > 180

    @staticmethod
    def _compile_search(pattern: str) -> re.Pattern | None:
        """Compile search pattern (regex or literal fallback)."""
        if not pattern:
            return None
        try:
            return re.compile(pattern, re.IGNORECASE)
        except re.error:
            return re.compile(re.escape(pattern), re.IGNORECASE)

    @staticmethod
    def _get_staleness_color(commit_date: datetime) -> str:
        """Return color name based on commit age.

        Green: < 30 days, Yellow: 30-90 days, Red: > 90 days.
        """
        age_days = (datetime.now(timezone.utc) - commit_date).days
        if age_days < 30:
            return "green"
        if age_days < 90:
            return "yellow"
        return "red"

    @staticmethod
    def _is_within_age_limit(commit_date: datetime, max_age_days: int | None) -> bool:
        """Return True if branch age is within the given limit (or no limit set)."""
        if max_age_days is None or max_age_days <= 0:
            return True
        age_days = (datetime.now(timezone.utc) - commit_date).days
        return age_days <= max_age_days

    def _filtered_branches(self) -> list[BranchInfo]:
        """Return branches matching current search/author/age filter settings."""
        search = self.query_one("#search-input", Input).value
        author_sel = self.query_one("#author-select", Select)
        author: str | None = author_sel.value if isinstance(author_sel.value, str) else None
        age_sel = self.query_one("#age-select", Select)
        max_age_days: int | None = age_sel.value if isinstance(age_sel.value, int) else None

        search_re = self._compile_search(search)

        result = []
        for b in self.branches:
            if not self.show_protected and b.is_protected:
                continue
            if not self.show_blacklisted and b.is_blacklisted:
                continue
            if search_re and not search_re.search(b.name):
                continue
            if author and b.author != author:
                continue
            if not self._is_within_age_limit(b.commit_date, max_age_days):
                continue
            result.append(b)
        return result

    def _export_csv(self) -> None:
        import csv
        path = Path.cwd() / "branches.csv"
        rows = self._filtered_branches()
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["name", "author", "date", "age_days", "ahead", "behind"])
            for b in rows:
                age = (datetime.now(timezone.utc) - b.commit_date).days
                w.writerow([b.name, b.author, b.commit_date.strftime("%Y-%m-%d"), age, b.ahead, b.behind])
        self.notify(f"Exported {len(rows)} branches to {path}", timeout=5)

    def _export_json(self) -> None:
        import json
        path = Path.cwd() / "branches.json"
        rows = self._filtered_branches()
        data = []
        for b in rows:
            age = (datetime.now(timezone.utc) - b.commit_date).days
            data.append({
                "name": b.name, "author": b.author,
                "date": b.commit_date.strftime("%Y-%m-%d"),
                "age_days": age, "ahead": b.ahead, "behind": b.behind,
            })
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.notify(f"Exported {len(rows)} branches to {path}", timeout=5)

    def _toggle_remote(self) -> None:
        self.delete_remote = not self.delete_remote
        btn = self.query_one("#toggle-remote", Button)
        btn.label = "Remote: ON" if self.delete_remote else "Remote: OFF"
        btn.variant = "error" if self.delete_remote else "warning"
        self._update_status()

    def _toggle_dry_run(self) -> None:
        self.dry_run = not self.dry_run
        btn = self.query_one("#toggle-dry-run", Button)
        btn.label = "Dry Run: ON" if self.dry_run else "Dry Run: OFF"
        btn.variant = "success" if self.dry_run else "primary"
        self._update_status()

    def _push_undo(self, entry: dict[str, str]) -> None:
        """Push a batch of deleted branches onto the undo stack."""
        self._undo_stack.append(entry)

    def _pop_undo(self) -> dict[str, str] | None:
        """Pop and return the last undo entry, or None if empty."""
        if not self._undo_stack:
            return None
        return self._undo_stack.pop()

    def _restore_entries(self, entries: list[dict[str, str]]) -> None:
        """Restore a list of undo entries and notify the result."""
        ok, fail = 0, 0
        for entry in entries:
            for name, hash_val in entry.items():
                success, _ = restore_branch(self.repo_path, name, hash_val)
                ok += success
                fail += not success
        parts = [f"Restored {ok} branch(es)"]
        if fail:
            parts.append(f"{fail} failed")
        self.notify(" ".join(parts), timeout=5)
        asyncio.ensure_future(self._load_branches())

    def undo_deletion(self) -> None:
        """Restore the last batch of deleted branches."""
        entry = self._pop_undo()
        if entry is None:
            self.notify("Nothing to undo", severity="information", timeout=3)
            return
        self._restore_entries([entry])

    def undo_all(self) -> None:
        """Restore all deleted branches from the undo stack."""
        if not self._undo_stack:
            self.notify("Nothing to undo", severity="information", timeout=3)
            return
        entries = list(reversed(self._undo_stack))
        self._undo_stack.clear()
        self._restore_entries(entries)

    # ── Row selection actions ────────────────────────────────────────────

    def toggle_row(self) -> None:
        tree = self.query_one("#branch-table", Tree)
        node = tree.cursor_node
        if node is None or node.data is None:  # group node or nothing
            return
        branch_name = str(node.data)
        branch = next((b for b in self.branches if b.name == branch_name), None)
        if branch and (branch.is_protected or branch.is_blacklisted):
            return
        if branch_name in self.selected:
            self.selected.discard(branch_name)
        else:
            self.selected.add(branch_name)
        # Update label in place
        selected = branch_name in self.selected
        checked = "✓ " if selected else "  "
        age = _age_from(branch.commit_date) if branch else ""
        upstream = self._upstream_str(branch) if branch else "—"
        stale = " [red]! stale[/]" if branch and self._is_stale(branch) else ""
        node.label = f"{checked}[bold]{branch_name}[/]  [dim]{age}  {upstream}[/]{stale}"
        self._update_status()

    def select_all(self) -> None:
        selectable = {
            b.name for b in self.branches
            if not b.is_protected and not b.is_blacklisted
        }
        if self.selected & selectable:
            self.selected -= selectable
        else:
            self.selected |= selectable
        self._build_tree()
        self._update_status()

    def _on_delete_progress(self, current: int, total: int, branch: str) -> None:
        """Update status bar during batch delete."""
        self.query_one("#status-bar", Static).update(
            f"Deleting {current}/{total}: {branch}"
        )

    def delete_selected(self) -> None:
        if not self.selected:
            return

        to_delete = list(self.selected)

        if self.dry_run:
            self.notify(
                f"Dry Run: would delete {len(to_delete)} branch(es): {', '.join(to_delete)}",
                severity="information", timeout=8,
            )
            self.query_one("#status-bar", Static).update(
                f"Dry run: would delete {len(to_delete)} branch(es)"
            )
            return

        # Capture hashes for undo before deletion
        hashes: dict[str, str] = {
            b.name: b.commit_hash for b in self.branches if b.name in to_delete and b.commit_hash
        }

        async def handle_confirmation(confirmed: bool) -> None:
            if confirmed:
                self._push_undo(hashes)
                total = len(to_delete)
                failed_local: list[str] = []
                for i, name in enumerate(to_delete, 1):
                    self._on_delete_progress(i, total, name)
                    await asyncio.sleep(0)  # yield to let Textual render
                    result = delete_branches(self.repo_path, [name])
                    if result:
                        failed_local.extend(result)
                failed_remote: list[str] = []
                if self.delete_remote:
                    remote_targets = [n for n in to_delete if n not in failed_local]
                    remote_total = len(remote_targets)
                    for i, name in enumerate(remote_targets, 1):
                        self._on_delete_progress(i, remote_total, f"{name} (remote)")
                        await asyncio.sleep(0)  # yield to let Textual render
                        result = delete_remote_branches(self.repo_path, [name])
                        if result:
                            failed_remote.extend(result)
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
                        " ".join(parts) + " — press u to undo"
                    )
                self.selected.clear()
                asyncio.ensure_future(self._load_branches())

        self.app.push_screen(
            ConfirmationDialog(list(self.selected), delete_remote=self.delete_remote),
            handle_confirmation,
        )

    def toggle_protected(self) -> None:
        self.show_protected = not self.show_protected
        self._refresh_table()

    def toggle_blacklisted(self) -> None:
        self.show_blacklisted = not self.show_blacklisted
        self._refresh_table()

    def reload(self) -> None:
        self.selected.clear()
        asyncio.ensure_future(self._load_branches())


class MaintenanceContent(Vertical):
    """Maintenance tab: health display and git maintenance tasks."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        self._task_running = False
        super().__init__()

    def compose(self) -> ComposeResult:
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
            yield Static("", id="health-details", classes="health-stat")
            with Vertical(id="health-recommendations"):
                yield Label("", id="reco-0", classes="reco-item")
                yield Label("", id="reco-1", classes="reco-item")
                yield Label("", id="reco-2", classes="reco-item")

        with Horizontal(id="task-status-bar"):
            yield LoadingIndicator(id="task-spinner")
            yield Label("Idle — click a task below to run", id="task-status")

        with Vertical(id="tasks-section"):
            yield Label("Maintenance Tasks", classes="section-title")
            with Vertical(id="task-buttons"):
                with Horizontal(classes="task-row"):
                    yield Button("Prune Remote", id="prune-btn", classes="task-button", variant="default",
                                 tooltip="git remote prune origin — Remove stale remote-tracking refs.")
                    yield Button("Expire Reflog", id="reflog-btn", classes="task-button", variant="default",
                                 tooltip="git reflog expire --expire=90.days.ago")
                    yield Button("Repack", id="repack-btn", classes="task-button", variant="primary",
                                 tooltip="git repack -Ad — Reorganize pack files.")
                with Horizontal(classes="task-row"):
                    yield Button("Git GC", id="gc-btn", classes="task-button", variant="primary",
                                 tooltip="git gc — Compress revisions, remove loose objects.")
                    yield Button("GC Aggressive", id="gc-agg-btn", classes="task-button", variant="warning",
                                 tooltip="git gc --aggressive — Deep optimization; run quarterly.")
                    yield Button("Run All", id="all-btn", classes="task-button", variant="error",
                                 tooltip="Run Prune, Reflog, Repack, and GC in sequence.")

        yield RichLog(id="task-output", highlight=True, markup=True, max_lines=100)

        with Vertical(id="help-legend"):
            yield Label("What each operation does:", classes="section-title")
            yield Label("• Git GC — Standard housekeeping: compresses revisions and removes unreachable objects")
            yield Label("• GC Aggressive — Deep re-delta: takes longer but finds better compression")
            yield Label("• Repack — Restructures pack files without full GC overhead")
            yield Label("• Prune Remote — Cleans up local tracking refs for branches already deleted upstream")
            yield Label("• Expire Reflog — Drops reflog entries older than 90 days to free disk space")
            yield Label("• Run All — Runs all the above tasks in order (takes the longest)")

    def on_mount(self) -> None:
        self._update_health()

    # ── Health stats ────────────────────────────────────────────────────

    def _assess_health(self, stats: dict[str, str]) -> tuple[str, str, list[str]]:
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

        details = []
        try:
            sz = int(size)
            if sz:
                details.append(f"Loose: {count} ({sz} KiB)")
            else:
                details.append(f"Loose: {count}")
        except ValueError:
            details.append(f"Loose: {count}")
        try:
            sp = int(size_pack)
            pk = int(packs)
            details.append(f"Packed: {in_pack} ({sp} KiB, {pk} packs)")
        except ValueError:
            details.append(f"Packed: {in_pack}")
        try:
            sg = int(size_garbage)
            details.append(f"Garbage: {garbage} ({sg} KiB)")
        except ValueError:
            details.append(f"Garbage: {garbage}")
        details.append(f"Prune-packable: {prune_packable}")
        self.query_one("#health-details", Static).update(" · ".join(details))

        badge, css_class, recommendations = self._assess_health(stats)
        badge_widget = self.query_one("#health-status-badge", Label)
        badge_widget.update(badge)
        badge_widget.remove_class("good", "fair", "poor")
        badge_widget.add_class(css_class)

        reco_summary = self.query_one("#health-status-reco", Label)
        if recommendations:
            reco_summary.update(recommendations[0])
        else:
            reco_summary.update("Repo is healthy")

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
        self.query_one("#task-spinner", LoadingIndicator).display = True
        self.query_one("#task-status", Label).update("Refreshing health…")
        try:
            await asyncio.to_thread(self._update_health)
            self.query_one("#task-status", Label).update("Health refreshed")
        except Exception as e:
            self.query_one("#task-status", Label).update(f"Error: {e}")
        finally:
            self.query_one("#task-spinner", LoadingIndicator).display = False

    # ── Task execution ──────────────────────────────────────────────────

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
            status.styles.color = ""
        icon = "✗" if error else "✓"
        self.notify(f"{icon} {msg}", severity="error" if error else "information", timeout=5)
        rl = self.query_one("#task-output", RichLog)
        rl.write(f"[{'bold red' if error else 'bold green'}]{icon} {msg}[/]")

    def _on_output(self, line: str) -> None:
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

        if btn_id == "refresh-health":
            await self._refresh_health_async()
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

    def _execute_single(self, task_key: str, on_output) -> tuple[bool, str]:
        dispatcher = {
            "gc": lambda: run_gc(self.repo_path, on_output=on_output),
            "gc-agg": lambda: run_gc(self.repo_path, aggressive=True, on_output=on_output),
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
            ("Prune", lambda p: prune_remote(p, on_output=on_output)),
            ("Reflog", lambda p: expire_reflog(p, on_output=on_output)),
            ("Repack", lambda p: repack_objects(p, on_output=on_output)),
            ("GC", lambda p: run_gc(p, on_output=on_output)),
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


class StashContent(Vertical):
    """Stashes tab: list stashes with drop/apply/pop actions."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        self.stashes: list[StashInfo] = []
        self._selected_ref: str | None = None
        super().__init__()

    def compose(self) -> ComposeResult:
        yield DataTable(id="stash-table")
        with Horizontal(id="stash-actions"):
            yield Button("Drop", id="stash-drop", variant="error")
            yield Button("Apply", id="stash-apply", variant="primary")
            yield Button("Pop", id="stash-pop", variant="warning")
            yield Button("Refresh", id="stash-refresh", variant="default")
        yield Static(id="stash-status")

    def on_mount(self) -> None:
        table = self.query_one("#stash-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Ref", "Branch", "Message", "Date")
        self._load_stashes()

    def _load_stashes(self) -> None:
        self.stashes = list_stashes(self.repo_path)
        table = self.query_one("#stash-table", DataTable)
        table.clear()
        for s in self.stashes:
            msg = (s.message[:60] + "…") if len(s.message) > 60 else s.message
            table.add_row(s.ref, s.branch or "—", msg, s.date.strftime("%Y-%m-%d"))
        self.query_one("#stash-status", Static).update(f"{len(self.stashes)} stash(es)")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        row = self.query_one("#stash-table", DataTable).get_row(event.row_key)
        if row:
            self._selected_ref = str(row[0])
        else:
            self._selected_ref = None

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "stash-refresh":
            self._load_stashes()
            return
        if not self._selected_ref:
            self.query_one("#stash-status", Static).update("No stash selected")
            return
        status = self.query_one("#stash-status", Static)
        if btn_id == "stash-drop":
            ok, msg = await asyncio.to_thread(drop_stash, self.repo_path, self._selected_ref)
            status.update(msg)
            if ok:
                self._load_stashes()
        elif btn_id == "stash-apply":
            ok, msg = await asyncio.to_thread(apply_stash, self.repo_path, self._selected_ref)
            status.update(msg)
        elif btn_id == "stash-pop":
            ok, msg = await asyncio.to_thread(pop_stash, self.repo_path, self._selected_ref)
            status.update(msg)
            if ok:
                self._load_stashes()


class CommitAnalysisContent(Vertical):
    """Commits tab: commit log, author stats, and large commits per branch."""

    CSS = """
    CommitAnalysisContent {
        height: 1fr;
    }
    #commit-select-row > Label {
        width: auto;
        margin: 0 1 0 0;
    }
    #commit-select-row > Select {
        width: 1fr;
    }
    #commit-status {
        height: 1;
        padding: 0 1;
        color: $text-muted;
    }
    """

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        self.branch_names: list[str] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        with Horizontal(id="commit-select-row"):
            yield Label("Branch:")
            yield Select([], id="commit-branch-select", prompt="Select branch", allow_blank=True, compact=True)
            yield Button("Load", id="commit-load", classes="task-button", variant="primary")
        yield DataTable(id="commit-log-table")
        yield DataTable(id="commit-authors-table")
        yield DataTable(id="commit-hotspots-table")
        with Horizontal(classes="task-row"):
            yield Button("Log", id="commit-show-log", classes="task-button", variant="default")
            yield Button("Authors", id="commit-show-authors", classes="task-button", variant="default")
            yield Button("Hotspots", id="commit-show-hotspots", classes="task-button", variant="default")
        yield Static(id="commit-status")

    def on_mount(self) -> None:
        self._load_branch_names()
        self.query_one("#commit-authors-table", DataTable).display = False
        self.query_one("#commit-hotspots-table", DataTable).display = False
        # Init columns
        self.query_one("#commit-log-table", DataTable).add_columns("Hash", "Author", "Date", "Subject")
        self.query_one("#commit-authors-table", DataTable).add_columns("Author", "Commits", "Insertions", "Deletions", "First", "Last")
        self.query_one("#commit-hotspots-table", DataTable).add_columns("Hash", "Author", "Date", "Subject")

    def _load_branch_names(self) -> None:
        try:
            branches = list_branches(self.repo_path)
        except RuntimeError as e:
            self.query_one("#commit-status", Static).update(str(e))
            return
        self.branch_names = [b.name for b in branches]
        sel = self.query_one("#commit-branch-select", Select)
        sel.set_options([(b, b) for b in self.branch_names])

    def _show_only(self, which: str) -> None:
        """Show one DataTable, hide the others."""
        for name, visible in [("log", which == "log"), ("authors", which == "authors"), ("hotspots", which == "hotspots")]:
            self.query_one(f"#commit-{name}-table", DataTable).display = visible

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "commit-load":
            sel = self.query_one("#commit-branch-select", Select)
            if sel.value is Select.NULL:
                self.query_one("#commit-status", Static).update("Select a branch.")
                return
            branch = sel.value
            self._load_commits(branch)
        elif btn_id == "commit-show-log":
            self._show_only("log")
        elif btn_id == "commit-show-authors":
            self._show_only("authors")
        elif btn_id == "commit-show-hotspots":
            self._show_only("hotspots")

    def _load_commits(self, branch: str) -> None:
        status = self.query_one("#commit-status", Static)
        status.update("Loading...")
        commits = get_commit_log(self.repo_path, branch, limit=200)
        # Log table
        log_table = self.query_one("#commit-log-table", DataTable)
        log_table.clear()
        for c in commits:
            log_table.add_row(c.short_hash, c.author, c.date.strftime("%Y-%m-%d"), c.subject[:80])
        # Authors table
        authors = get_author_stats(self.repo_path, branch)
        auth_table = self.query_one("#commit-authors-table", DataTable)
        auth_table.clear()
        for a in authors:
            auth_table.add_row(a.author, str(a.commits), f"+{a.insertions}", f"-{a.deletions}",
                               a.first_date.strftime("%Y-%m-%d"), a.last_date.strftime("%Y-%m-%d"))
        # Hotspots table
        large = get_large_commits(self.repo_path, branch, threshold=50)
        hot_table = self.query_one("#commit-hotspots-table", DataTable)
        hot_table.clear()
        for c in large:
            hot_table.add_row(c.short_hash, c.author, c.date.strftime("%Y-%m-%d"), c.subject[:80])
        self._show_only("log")
        status.update(f"{len(commits)} commits · {len(authors)} authors · {len(large)} large")


class PRIntegrationContent(Vertical):
    """Pull Requests tab: show open PRs/MRs from GitHub or GitLab."""

    CSS = """
    PRIntegrationContent {
        height: 1fr;
    }
    """

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        self.prs: list[PRInfo] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        yield DataTable(id="pr-table")
        with Horizontal(id="pr-actions", classes="task-row"):
            yield Button("Open in Browser", id="pr-open", classes="task-button", variant="primary")
            yield Button("Refresh", id="pr-refresh", classes="task-button", variant="default")
            yield Static(id="pr-status")

    def on_mount(self) -> None:
        table = self.query_one("#pr-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Branch", "PR", "Title", "Author", "State")
        self._load_prs()

    def _load_prs(self) -> None:
        status = self.query_one("#pr-status", Static)
        provider = _detect_provider(self.repo_path)
        if not provider:
            status.update("No GitHub/GitLab remote detected.")
            return
        token = _get_api_token(provider)
        if not token:
            env = "GITHUB_TOKEN" if provider == "github" else "GITLAB_TOKEN"
            status.update(f"Set {env} env var to enable PR integration.")
            return
        self.prs = list_open_prs(self.repo_path)
        table = self.query_one("#pr-table", DataTable)
        table.clear()
        for pr in self.prs:
            table.add_row(pr.branch, f"#{pr.number}", pr.title[:60], pr.author, pr.state)
        status.update(f"{len(self.prs)} open {'PR' if provider == 'github' else 'MR'}(s) — {provider}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "pr-refresh":
            self._load_prs()
        elif btn_id == "pr-open":
            table = self.query_one("#pr-table", DataTable)
            if table.cursor_row is not None and table.cursor_row < len(self.prs):
                import webbrowser
                webbrowser.open(self.prs[table.cursor_row].url)


class StaleReposContent(Vertical):
    """Stale Branches tab: show stale branches across all bookmarked repos."""

    CSS = """
    StaleReposContent {
        height: 1fr;
    }
    """

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        self.branches: list = []
        super().__init__()

    def compose(self) -> ComposeResult:
        yield DataTable(id="stale-table")
        with Horizontal(id="stale-actions", classes="task-row"):
            yield Button("Refresh", id="stale-refresh", classes="task-button", variant="default")
            yield Static(id="stale-status")

    def on_mount(self) -> None:
        table = self.query_one("#stale-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Repo", "Branch", "Age", "Author", "Last Commit")
        self._load()

    def _load(self) -> None:
        from git_cleaner.config import load_bookmarks

        bookmarks = load_bookmarks()
        # Include current repo if not already bookmarked
        current = str(self.repo_path.resolve())
        repos = list(bookmarks)
        if current not in repos:
            repos.insert(0, current)

        status = self.query_one("#stale-status", Static)
        status.update(f"Scanning {len(repos)} repo(s)…")
        self.branches = get_stale_branches_across_repos(repos)
        table = self.query_one("#stale-table", DataTable)
        table.clear()
        for b in self.branches:
            repo_label = Path(b.repo).name
            table.add_row(repo_label, b.name, f"{b.age_days}d", b.author, b.last_commit)
        status.update(f"{len(self.branches)} stale branch(es) across {len(repos)} repo(s)")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "stale-refresh":
            self._load()


class CompareContent(Vertical):
    """Compare tab: select two branches and see their diff."""

    CSS = """
    CompareContent {
        height: 1fr;
    }
    #compare-select-row > Label {
        width: auto;
        margin: 0 1 0 0;
    }
    """

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        self.branch_names: list[str] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        with Horizontal(id="compare-select-row"):
            yield Label("Source:")
            yield Select([], id="compare-base", prompt="Select source branch", allow_blank=True, compact=True)
            yield Label("Target:")
            yield Select([], id="compare-target", prompt="Select target branch", allow_blank=True, compact=True)
            yield Button("Compare", id="compare-run", variant="primary", classes="task-button")
        yield Static("Select two branches and press Compare.", id="compare-result")
        with Horizontal(id="compare-actions"):
            yield Label("", id="compare-summary")

    def on_mount(self) -> None:
        self._load_branch_names()

    def _load_branch_names(self) -> None:
        try:
            branches = list_branches(self.repo_path)
        except RuntimeError as e:
            self.query_one("#compare-summary", Label).update(str(e))
            return
        self.branch_names = [b.name for b in branches]
        base_sel = self.query_one("#compare-base", Select)
        target_sel = self.query_one("#compare-target", Select)
        base_sel.set_options([(n, n) for n in self.branch_names])
        target_sel.set_options([(n, n) for n in self.branch_names])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "compare-run":
            self._run_comparison()

    def _run_comparison(self) -> None:
        base_sel = self.query_one("#compare-base", Select)
        target_sel = self.query_one("#compare-target", Select)
        if base_sel.value is Select.NULL or target_sel.value is Select.NULL:
            self.query_one("#compare-summary", Label).update("Select both branches.")
            return
        base = base_sel.value
        target = target_sel.value
        if base == target:
            self.query_one("#compare-summary", Label).update("Select two different branches.")
            return

        try:
            merge_base = get_merge_base(self.repo_path, base, target)
        except RuntimeError as e:
            self.query_one("#compare-summary", Label).update(f"Error: {e}")
            return

        ahead, behind = get_commits_symmetric(self.repo_path, base, target)
        stats = get_diff_stat(self.repo_path, base, target)
        summary = get_shortstat(self.repo_path, base, target)

        lines = [f"[bold]{base}[/] ↔ [bold]{target}[/]  (merge-base: {merge_base[:8]})"]
        total_commits = len(ahead) + len(behind)
        if total_commits == 0:
            lines.append("\n[bold]No differences[/] — branches are identical.")
        else:
            lines.append(
                f"\n[bold]Summary:[/] {summary}  "
                f"[green]+{len(ahead)} ahead[/] [red]-{len(behind)} behind[/]"
            )
            if ahead:
                lines.append(f"\n[bold]{base} ahead ({len(ahead)}):[/]")
                for sha, subject in ahead[:30]:
                    lines.append(f"  [green]>[/] {sha}  {subject}")
                if len(ahead) > 30:
                    lines.append(f"  ... and {len(ahead) - 30} more")
            if behind:
                lines.append(f"\n[bold]{target} ahead ({len(behind)}):[/]")
                for sha, subject in behind[:30]:
                    lines.append(f"  [red]<[/] {sha}  {subject}")
                if len(behind) > 30:
                    lines.append(f"  ... and {len(behind) - 30} more")
        if stats:
            lines.append(f"\n[bold]Files changed ({len(stats)}):[/]")
            for added, removed, path in stats[:50]:
                delta = f"+{added}/-{removed}" if added != "-" else "binary"
                lines.append(f"  {delta:>10}  {path}")
            if len(stats) > 50:
                lines.append(f"  ... and {len(stats) - 50} more")
        self.query_one("#compare-summary", Label).update(
            f"{total_commits} commit(s), {len(stats)} file(s)"
        )
        self.query_one("#compare-result", Static).update("\n".join(lines))


class WorktreeCreateDialog(ModalScreen[tuple[str, str] | None]):
    """Modal to create a new worktree."""

    CSS = """
    WorktreeCreateDialog {
        align: center middle;
    }
    #wt-create-dialog {
        width: 60;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }
    #wt-create-dialog > Label {
        text-style: bold;
        margin-bottom: 1;
    }
    #wt-create-dialog > Input {
        margin: 0 0 1 0;
    }
    #wt-create-buttons {
        margin-top: 1;
    }
    #wt-create-buttons Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Create Worktree"),
            Input(placeholder="Path (e.g. ../my-feature)", id="wt-path-input"),
            Input(placeholder="New branch name (optional)", id="wt-branch-input"),
            Horizontal(
                Button("Cancel", variant="default", id="wt-cancel"),
                Button("Create", variant="primary", id="wt-create"),
            ),
            id="wt-create-dialog",
        )

    def on_mount(self) -> None:
        self.query_one("#wt-path-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "wt-cancel":
            self.dismiss(None)
        elif event.button.id == "wt-create":
            path = self.query_one("#wt-path-input", Input).value.strip()
            branch = self.query_one("#wt-branch-input", Input).value.strip()
            if not path:
                return
            self.dismiss((path, branch))

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            path = self.query_one("#wt-path-input", Input).value.strip()
            branch = self.query_one("#wt-branch-input", Input).value.strip()
            if path:
                self.dismiss((path, branch))


class WorktreesContent(Vertical):
    """Worktrees tab: list, create, and remove git worktrees."""

    CSS = """
    WorktreesContent {
        height: 1fr;
    }
    """

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        self.worktrees: list[WorktreeInfo] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        yield DataTable(id="wt-table")
        with Horizontal(id="wt-actions", classes="task-row"):
            yield Button("Add", id="wt-add", classes="task-button", variant="primary")
            yield Button("Remove", id="wt-remove", classes="task-button", variant="error")
            yield Button("Prune", id="wt-prune", classes="task-button", variant="warning")
            yield Button("Refresh", id="wt-refresh", classes="task-button", variant="default")
            yield Static(id="wt-status")

    def on_mount(self) -> None:
        table = self.query_one("#wt-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Path", "Branch", "HEAD", "Status")
        self._load_worktrees()

    def _load_worktrees(self) -> None:
        self.worktrees = list_worktrees(self.repo_path)
        table = self.query_one("#wt-table", DataTable)
        table.clear()
        for wt in self.worktrees:
            if wt.is_bare:
                branch = "(bare)"
            elif wt.is_detached:
                branch = "(detached)"
            else:
                branch = wt.branch or "—"
            head = wt.head[:8] if wt.head else "—"
            status = ""
            if wt.is_locked:
                status = f"locked: {wt.lock_reason}" if wt.lock_reason else "locked"
            elif wt.is_prunable:
                status = f"prunable: {wt.prune_reason}" if wt.prune_reason else "prunable"
            table.add_row(wt.path, branch, head, status)
        self.query_one("#wt-status", Static).update(f"{len(self.worktrees)} worktree(s)")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "wt-refresh":
            self._load_worktrees()
            return
        if btn_id == "wt-prune":
            ok, msg = await asyncio.to_thread(prune_worktrees, self.repo_path, dry_run=False)
            self.query_one("#wt-status", Static).update(f"Prune: {msg}")
            self._load_worktrees()
            return
        if btn_id == "wt-add":
            self.app.push_screen(WorktreeCreateDialog(), self._on_add_created)
            return
        if btn_id == "wt-remove":
            table = self.query_one("#wt-table", DataTable)
            if table.cursor_row is None or table.cursor_row >= len(self.worktrees):
                self.query_one("#wt-status", Static).update("No worktree selected")
                return
            wt = self.worktrees[table.cursor_row]
            if wt.is_bare:
                self.query_one("#wt-status", Static).update("Cannot remove the main worktree")
                return
            self.app.push_screen(
                ConfirmationDialog([wt.path], delete_remote=False),
                lambda confirmed: asyncio.ensure_future(self._do_remove(wt.path, confirmed)),
            )

    async def _do_remove(self, path: str, confirmed: bool) -> None:
        if not confirmed:
            return
        ok, msg = await asyncio.to_thread(remove_worktree, self.repo_path, path, force=True)
        self.query_one("#wt-status", Static).update(msg)
        self._load_worktrees()

    def _on_add_created(self, result: tuple[str, str] | None) -> None:
        if result:
            path, branch = result
            ok, msg = asyncio.get_event_loop().run_until_complete(
                asyncio.to_thread(add_worktree, self.repo_path, path, branch or None)
            )
            self.query_one("#wt-status", Static).update(msg)
            self._load_worktrees()


class MainScreen(Screen):
    """Single screen with tabbed content: Branches, Maintenance, Stashes."""

    BINDINGS = [
        Binding("space", "toggle_row", "Toggle selection"),
        Binding("a", "select_all", "Select all"),
        Binding("d", "delete_selected", "Delete selected"),
        Binding("p", "toggle_protected", "Toggle protected visibility"),
        Binding("b", "toggle_blacklisted", "Toggle blacklisted visibility"),
        Binding("r", "toggle_remote", "Toggle remote deletion"),
        Binding("ctrl+r", "reload", "Reload"),
        Binding("u", "undo_deletion", "Undo"),
        Binding("U", "undo_all", "Undo all"),
        Binding("ctrl+b", "bookmarks", "Bookmarks"),
        Binding("question", "show_help", "Help"),
        Binding("h", "show_help", "Help"),
        Binding("H", "show_undo_history", "Undo history"),
    ]

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        super().__init__()
        self.title = "Git Cleaner"

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Branches", id="branches-pane"):
                yield BranchesContent(self.repo_path)
            with TabPane("Maintenance", id="maintenance-pane"):
                yield MaintenanceContent(self.repo_path)
            with TabPane("Stashes", id="stash-pane"):
                yield StashContent(self.repo_path)
            with TabPane("Commits", id="commits-pane"):
                yield CommitAnalysisContent(self.repo_path)
            with TabPane("Compare", id="compare-pane"):
                yield CompareContent(self.repo_path)
            with TabPane("Worktrees", id="worktrees-pane"):
                yield WorktreesContent(self.repo_path)
            with TabPane("Pull Requests", id="pullrequests-pane"):
                yield PRIntegrationContent(self.repo_path)
            with TabPane("Stale", id="stale-pane"):
                yield StaleReposContent(self.repo_path)
        yield RepoFooter(self.repo_path)

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        if event.pane.id == "compare-pane":
            self.query_one(CompareContent)._load_branch_names()
        elif event.pane.id == "commits-pane":
            self.query_one(CommitAnalysisContent)._load_branch_names()

    # ── Actions that delegate to BranchesContent ────────────────────────

    def action_toggle_row(self) -> None:
        self.query_one(BranchesContent).toggle_row()

    def action_select_all(self) -> None:
        self.query_one(BranchesContent).select_all()

    def action_delete_selected(self) -> None:
        self.query_one(BranchesContent).delete_selected()

    def action_toggle_protected(self) -> None:
        self.query_one(BranchesContent).toggle_protected()

    def action_toggle_blacklisted(self) -> None:
        self.query_one(BranchesContent).toggle_blacklisted()

    def action_toggle_remote(self) -> None:
        self.query_one(BranchesContent)._toggle_remote()

    def action_reload(self) -> None:
        self.query_one(BranchesContent).reload()

    def action_undo_deletion(self) -> None:
        self.query_one(BranchesContent).undo_deletion()

    def action_undo_all(self) -> None:
        """Undo all delete operations."""
        self.query_one(BranchesContent).undo_all()

    def action_bookmarks(self) -> None:
        self.app.push_screen(RepoSwitcher(self.repo_path), self._on_switch_repo)

    def action_show_help(self) -> None:
        self.app.push_screen(HelpOverlay())

    def action_show_undo_history(self) -> None:
        """Show undo history modal."""
        branches = self.query_one(BranchesContent)
        self.app.push_screen(UndoHistory(branches._undo_stack))

    def _on_switch_repo(self, path: str | None) -> None:
        if path:
            self.app.switch_repo(path)


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

    def on_mount(self) -> None:
        self.query_one("#confirm", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


class RepoSwitcher(ModalScreen[str | None]):
    """Modal to manage bookmarked repos and switch between them."""

    def __init__(self, current: Path) -> None:
        self.current = current
        super().__init__()
        self.title = "Repositories"

    def compose(self) -> ComposeResult:
        current_path = str(self.current.resolve())
        with Vertical(id="dialog"):
            yield Label("Bookmarked Repositories (Ctrl+B)")
            bookmarks = load_bookmarks()
            if bookmarks:
                yield ListView(
                    *(ListItem(Static(f"{b}{'  ✓' if b == current_path else ''}")) for b in bookmarks),
                    id="repo-list",
                )
            else:
                yield Label("  No bookmarks yet — press 'Add current' to add this repo.")
            with Horizontal():
                yield Button("Add current", id="repo-add", variant="primary")
                yield Button("Remove current", id="repo-remove", variant="warning")
                yield Button("Close", id="repo-close", variant="default")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        bookmarks = load_bookmarks()
        if event.item:
            idx = event.list_view.index
            if idx is not None and idx < len(bookmarks):
                self.dismiss(bookmarks[idx])

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "repo-add":
            add_bookmark(str(self.current.resolve()))
            self.dismiss(None)
            self.app.notify("Bookmark added — reopen list to see it")
        elif btn_id == "repo-remove":
            remove_bookmark(str(self.current.resolve()))
            self.dismiss(None)
            self.app.notify("Bookmark removed")
        elif btn_id == "repo-close":
            self.dismiss(None)


class HelpOverlay(ModalScreen[None]):
    """Modal screen showing all keyboard shortcuts.

    Generates content from MainScreen.BINDINGS so it stays in sync.
    """

    CSS = """
    HelpOverlay {
        align: center middle;
    }

    #help-container {
        width: 70;
        max-height: 80%;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    #help-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    .help-section-title {
        text-style: bold;
        margin-bottom: 0;
    }

    .help-item {
        margin: 0;
        padding-left: 2;
    }
    """

    # ponytail: navigation keys are DataTable built-ins, not in MainScreen.BINDINGS
    _NAV_HELP = [
        "[up/k] Move up",
        "[down/j] Move down",
        "[pageup] Page up",
        "[pagedown] Page down",
        "[home/g] Go to top",
        "[end/G] Go to bottom",
    ]

    @staticmethod
    def _format_key(key: str) -> str:
        """Format a textual key name into a human-readable label."""
        return f"[{key}]"

    def compose(self) -> ComposeResult:
        items = [
            Label("Keyboard Shortcuts", id="help-title"),
            Static("Navigation", classes="help-section-title"),
        ]
        for line in self._NAV_HELP:
            items.append(Static(line, classes="help-item"))

        items.append(Static("Actions", classes="help-section-title"))
        for binding in MainScreen.BINDINGS:
            if binding.key == "question":
                continue  # merged into h below
            if binding.key == "h":
                items.append(Static(f"[?] or [h] {binding.description}", classes="help-item"))
                continue
            items.append(Static(
                f"{self._format_key(binding.key)} {binding.description}",
                classes="help-item",
            ))
        items.append(Static("Compare Tab", classes="help-section-title"))
        items.append(Static("[Tab] Switch to Compare tab", classes="help-item"))
        items.append(Static("Select base & target branches, press Compare", classes="help-item"))

        items.append(Static("Commits Tab", classes="help-section-title"))
        items.append(Static("[Tab] Switch to Commits tab", classes="help-item"))
        items.append(Static("Select branch, press Load to view commit log", classes="help-item"))
        items.append(Static("Toggle Log / Authors / Hotspots buttons", classes="help-item"))

        items.append(Static("Worktrees Tab", classes="help-section-title"))
        items.append(Static("[Tab] Switch to Worktrees tab", classes="help-item"))
        items.append(Static("[Enter] Select worktree row", classes="help-item"))

        items.append(Static("Pull Requests Tab", classes="help-section-title"))
        items.append(Static("[Tab] Switch to Pull Requests tab", classes="help-item"))
        items.append(Static("Requires GITHUB_TOKEN or GITLAB_TOKEN env var", classes="help-item"))
        items.append(Static("[Enter] Open selected PR in browser", classes="help-item"))

        items.append(Static("Stale Tab", classes="help-section-title"))
        items.append(Static("[Tab] Switch to Stale tab", classes="help-item"))
        items.append(Static("Shows stale branches (>180d) across all bookmarked repos", classes="help-item"))

        items.append(Static("[escape] Close", classes="help-item"))
        yield Vertical(*items, id="help-container")

    def on_key(self, event: Key) -> None:
        """Close overlay on any key press."""
        self.dismiss()


class UndoHistory(ModalScreen[None]):
    """Modal screen showing undo history — what branches can be restored."""

    CSS = """
    UndoHistory {
        align: center middle;
    }

    #undo-history-container {
        width: 60;
        max-height: 80%;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    #undo-history-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    """

    def __init__(self, undo_stack: list[dict[str, str]]) -> None:
        super().__init__()
        self.undo_stack = undo_stack

    def compose(self) -> ComposeResult:
        items = [Label("Undo History", id="undo-history-title")]
        for i, entry in enumerate(reversed(self.undo_stack), 1):
            for branch, _hash in entry.items():
                items.append(Static(f"{i}. {branch}"))
        if not self.undo_stack:
            items.append(Static("Nothing to undo."))
        items.append(Static("\nPress any key to close"))
        yield Vertical(*items, id="undo-history-container")

    def on_key(self, event: Key) -> None:
        """Close overlay on any key press."""
        self.dismiss()


class GitCleanerApp(App):
    """Main TUI application for git branch cleaning."""

    CSS = GIT_CLEANER_CSS

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        super().__init__()
        self.theme = load_theme()

    def on_mount(self) -> None:
        self.push_screen(MainScreen(self.repo_path))

    def watch_theme(self, old: str, new: str) -> None:
        """Persist theme whenever it changes (e.g. via Ctrl+T toggle)."""
        save_theme(new)

    def switch_repo(self, new_path: str) -> None:
        """Replace the screen tree with a fresh MainScreen for a different repo."""
        self.repo_path = Path(new_path)
        self.pop_screen()
        self.push_screen(MainScreen(self.repo_path))
