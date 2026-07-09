import asyncio
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

import whenever

from textual import on
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

/* === Tab styling (match the Option B mockup) === */
ContentTabs {
    background: $surface 50%;
    height: 3;
}

Tab {
    width: auto;
    height: 3;
    padding: 0 2;
    text-align: center;
    color: $text-muted;
    text-style: bold;
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

/* === Main content vertical centering === */
#main-content {
    align: center top;
    height: 1fr;
    width: 100%;
    overflow-y: auto;
}

/* === Date range picker labels === */
#lbl-from, #lbl-until {
    color: $text-muted;
    width: 6;
    text-align: right;
    padding: 0 1 0 0;
}

/* === Date picker + Load button row === */
#date-btn-row {
    height: auto;
    align: center middle;
    margin: 0 1;
}

#date-btn-row > #load-btn {
    margin: 0 0 0 2;
}

.preset-btn {
    margin: 0 0 0 1;
    min-width: 5;
    height: 3;
}

/* === Filter row: search + author === */
#filter-row {
    height: auto;
    margin: 0 1 0 1;
    align: left middle;
}

#search-input {
    width: 1fr;
    min-width: 20;
}

#author-select {
    width: 28;
    min-width: 16;
    margin: 0 0 0 2;
}

/* === Error / status messages === */
#status-bar {
    height: 1;
    padding: 0 2;
    color: $text-muted;
}

/* === Action row (remote toggle) === */
#action-row {
    height: auto;
    margin: 0 0 0 2;
    align: left middle;
    width: 100%;
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

/* === Branch table === */
#branch-table {
    height: 1fr;
    margin: 0 1 0 1;
    width: 100%;
}

#details-pane {
    height: auto;
    max-height: 12;
    margin: 0 1;
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
    padding: 1 0;
    height: 1fr;
}

/* === Maintenance pane === */
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

/* === Export row === */
#export-row {
    height: auto;
    margin: 0 0 0 2;
    align: left middle;
}

#export-row Button {
    min-width: 8;
    margin: 0 1 0 0;
}

/* === Stash browser === */
#stash-table {
    height: 1fr;
    margin: 0 1;
}

#stash-actions {
    height: auto;
    margin: 0 1;
    align: center middle;
}

#stash-actions Button {
    margin: 0 1;
    min-width: 10;
}

#stash-status {
    height: 1;
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

/* === Bottom repo label === */
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

.footer-repo-label {
    color: $text-muted;
    padding: 0 1;
    height: 1;
    text-align: left;
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
        self._deleted_branches: dict[str, str] = {}
        super().__init__()

    def compose(self) -> ComposeResult:
        with Horizontal(id="date-btn-row"):
            yield DateRangePicker(id="date-picker")
            yield Button("Load Branches", id="load-btn", variant="primary")
            yield Button("7d", id="preset-7d", classes="preset-btn")
            yield Button("30d", id="preset-30d", classes="preset-btn")
            yield Button("90d", id="preset-90d", classes="preset-btn")
            yield Button("1y", id="preset-1y", classes="preset-btn")
        with Horizontal(id="filter-row"):
            yield Input(placeholder="Search branches...", id="search-input")
            yield Select([], id="author-select", prompt="All authors", allow_blank=True)
        yield Tree("", id="branch-table")
        yield Vertical(Static("Click a branch to see details", id="details-content"), id="details-pane")
        with Horizontal(id="action-row"):
            yield Button("Remote: OFF", id="toggle-remote", variant="default")
            yield Button("Dry Run: OFF", id="toggle-dry-run", variant="default")
        with Horizontal(id="export-row"):
            yield Button("CSV", id="export-csv", variant="default")
            yield Button("JSON", id="export-json", variant="default")
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
    def _on_author_changed(self, event: Select.Changed) -> None:
        if event.select.id == "author-select":
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

    def _add_branch_node(self, parent, b: BranchInfo) -> None:
        """Add a branch leaf node to a tree parent."""
        selected = b.name in self.selected
        checked = "✓ " if selected else "  "
        upstream = self._upstream_str(b)
        age = _age_from(b.commit_date)
        stale = " [red]! stale[/]" if self._is_stale(b) else ""
        label = f"{checked}[bold]{b.name}[/]  [dim]{age}  {upstream}[/]{stale}"
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

    def _filtered_branches(self) -> list[BranchInfo]:
        """Return branches matching current search/author/filter settings."""
        search = self.query_one("#search-input", Input).value.lower()
        author_sel = self.query_one("#author-select", Select)
        author: str | None = author_sel.value
        result = []
        for b in self.branches:
            if not self.show_protected and b.is_protected:
                continue
            if not self.show_blacklisted and b.is_blacklisted:
                continue
            if search and search not in b.name.lower():
                continue
            if author and b.author != author:
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
        btn.variant = "primary" if self.delete_remote else "default"
        self._update_status()

    def _toggle_dry_run(self) -> None:
        self.dry_run = not self.dry_run
        btn = self.query_one("#toggle-dry-run", Button)
        btn.label = "Dry Run: ON" if self.dry_run else "Dry Run: OFF"
        btn.variant = "error" if self.dry_run else "default"
        self._update_status()

    def undo_deletion(self) -> None:
        """Restore the last batch of deleted branches."""
        if not self._deleted_branches:
            self.notify("Nothing to undo", severity="information", timeout=3)
            return
        ok, fail = 0, 0
        for name, hash_val in list(self._deleted_branches.items()):
            success, msg = restore_branch(self.repo_path, name, hash_val)
            if success:
                ok += 1
            else:
                fail += 1
        parts = [f"Restored {ok} branch(es)"]
        if fail:
            parts.append(f"{fail} failed")
        self._deleted_branches.clear()
        self.notify(" ".join(parts), timeout=5)
        asyncio.ensure_future(self._load_branches())

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

        def handle_confirmation(confirmed: bool) -> None:
            if confirmed:
                self._deleted_branches = hashes
                failed_local = delete_branches(self.repo_path, to_delete)
                failed_remote: list[str] = []
                if self.delete_remote:
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
            yield Label("", id="stat-loose", classes="health-stat")
            yield Label("", id="stat-packed", classes="health-stat")
            yield Label("", id="stat-garbage", classes="health-stat")
            yield Label("", id="stat-prune", classes="health-stat")
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
                    yield Button("Git GC", id="gc-btn", classes="task-button", variant="primary",
                                 tooltip="git gc — Compress revisions, remove loose objects.")
                    yield Button("GC Aggressive", id="gc-agg-btn", classes="task-button", variant="warning",
                                 tooltip="git gc --aggressive — Deep optimization; run quarterly.")
                    yield Button("Repack", id="repack-btn", classes="task-button", variant="primary",
                                 tooltip="git repack -Ad — Reorganize pack files.")
                with Horizontal(classes="task-row"):
                    yield Button("Prune Remote", id="prune-btn", classes="task-button", variant="default",
                                 tooltip="git remote prune origin — Remove stale remote-tracking refs.")
                    yield Button("Expire Reflog", id="reflog-btn", classes="task-button", variant="default",
                                 tooltip="git reflog expire --expire=90.days.ago")
                    yield Button("Run All", id="all-btn", classes="task-button", variant="error",
                                 tooltip="Run GC, Repack, Prune Remote, and Expire Reflog in sequence.")

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

        try:
            sz = int(size)
            loose_extra = f" ({sz} KiB)" if sz else ""
        except ValueError:
            loose_extra = ""
        self.query_one("#stat-loose", Label).update(f"Loose objects: {count}{loose_extra}")

        try:
            sp = int(size_pack)
            pk = int(packs)
            packed_extra = f" ({sp} KiB in {pk} packs)" if pk else ""
        except ValueError:
            packed_extra = ""
        self.query_one("#stat-packed", Label).update(f"Packed objects: {in_pack}{packed_extra}")

        try:
            sg = int(size_garbage)
            garbage_extra = f" ({sg} KiB)" if sg else ""
        except ValueError:
            garbage_extra = ""
        self.query_one("#stat-garbage", Label).update(f"Garbage objects: {garbage}{garbage_extra}")
        self.query_one("#stat-prune", Label).update(f"Prune-packable: {prune_packable}")

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

    @on(DataTable.RowHighlighted)
    def _on_stash_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is None:
            self._selected_ref = None
            return
        row = self.query_one("#stash-table", DataTable).get_row(event.row_key)
        if row:
            self._selected_ref = str(row[0])

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
        Binding("ctrl+b", "bookmarks", "Bookmarks"),
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
        yield RepoFooter(self.repo_path)

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

    def action_bookmarks(self) -> None:
        self.app.push_screen(RepoSwitcher(self.repo_path), self._on_switch_repo)

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
