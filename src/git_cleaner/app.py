import calendar as cal_mod
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header,
    Footer,
    Button,
    Label,
    Static,
    DataTable,
)
from textual.containers import Horizontal, Vertical, Grid
from textual.binding import Binding

from git_cleaner.config import (
    get_protected_patterns,
    get_blacklist_patterns,
    matches_any,
)
from git_cleaner.git_ops import (
    BranchInfo,
    list_branches,
    delete_branches,
    get_repo_root,
)

DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class DayButton(Button):
    """A button representing a day in the calendar."""

    def __init__(self, day_num: int, **kwargs) -> None:
        self.day_num = day_num
        super().__init__(str(day_num), **kwargs)

GIT_CLEANER_CSS = """
Screen {
    align: center middle;
}

Header {
    background: $primary 20%;
}

Footer {
    background: $primary 10%;
}

/* === Main content vertical centering === */
#main-content {
    align: center middle;
    height: 1fr;
    width: 100%;
}

/* === Title === */
#title {
    text-style: bold;
    text-align: center;
    padding: 0 1;
    height: 3;
    color: $primary;
}

#repo-label {
    padding: 0 1;
    color: $text-muted;
    text-align: center;
    height: 1;
}

/* === Date display row === */
#date-display {
    height: auto;
    margin: 0 0 1 0;
    align: center middle;
    background: $surface;
    padding: 0 1;
    min-width: 40;
}

.date-val {
    padding: 0 2 0 0;
}

#from-date-label {
    color: $secondary;
    text-style: bold;
}

#until-date-label {
    color: $accent;
    text-style: bold;
}

/* === Calendar navigation === */
#cal-nav {
    height: auto;
    margin: 1 0 0 0;
    align: center middle;
}

#cal-prev, #cal-next {
    width: 5;
    min-width: 5;
}

.cal-label {
    width: 22;
    text-align: center;
    text-style: bold;
    padding: 0 1;
}

/* === Day-of-week headers === */
#cal-dow {
    height: auto;
    align: center middle;
    margin: 0 0;
}

.dow-label {
    width: 9;
    text-align: center;
    color: $text-muted;
    text-style: bold;
}

/* === Calendar day grid === */
#cal-grid {
    grid-size: 7;
    grid-gutter: 0;
    width: 72;
    height: auto;
    align: center middle;
}

.day {
    width: 10;
    height: 3;
    margin: 0;
    border: tall $surface;
}

.day:hover {
    border: tall $primary 50%;
}

.day-blank {
    width: 10;
    height: 3;
}

.day.selected-from {
    background: $secondary 35%;
    border: tall $secondary;
    color: $text;
}

.day.selected-until {
    background: $accent 35%;
    border: tall $accent;
    color: $text;
}

.day.selected-range {
    background: $primary 20%;
    border: tall $primary 30%;
}

/* === Centering wrapper === */
.center-row {
    align: center middle;
    height: auto;
    width: 100%;
}

/* === Mode toggle buttons === */
#select-mode {
    height: auto;
    margin: 1 0;
    align: center middle;
}

#mode-from, #mode-until {
    margin: 0 1;
    min-width: 18;
}

/* === Load button === */
#load-btn {
    width: 24;
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

#branch-table {
    height: 1fr;
    margin: 0 1;
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
    width: 60;
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
"""


class CalendarScreen(Screen):
    """Screen with an interactive calendar date picker."""

    def __init__(self, repo_path: Path) -> None:
        super().__init__()
        self.repo_path = repo_path
        self.from_date = None
        self.until_date = None
        self.view_date = date.today().replace(day=1)
        self._date_mode = "from"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-content"):
            yield Label("Git Branch Cleaner", id="title")
            yield Label(f"Repository: {self.repo_path}", id="repo-label")

            with Horizontal(id="date-display"):
                from_text = self.from_date.isoformat() if self.from_date else "Not set"
                until_text = self.until_date.isoformat() if self.until_date else "Not set"
                yield Label("From: ", id="from-label")
                yield Label(from_text, id="from-date-label", classes="date-val")
                yield Label("  Until: ", id="until-label")
                yield Label(until_text, id="until-date-label", classes="date-val")

            with Horizontal(id="cal-nav"):
                yield Button("<", id="cal-prev")
                yield Label(
                    self.view_date.strftime("%B %Y"), id="cal-month", classes="cal-label"
                )
                yield Button(">", id="cal-next")

            with Horizontal(id="cal-dow"):
                for d in DOW:
                    yield Label(d, classes="dow-label")

            with Horizontal(classes="center-row"):
                with Grid(id="cal-grid"):
                    cal = cal_mod.monthcalendar(
                        self.view_date.year, self.view_date.month
                    )
                    for week in cal:
                        for day_num in week:
                            if day_num == 0:
                                yield Button("", disabled=True, classes="day-blank")
                            else:
                                day = date(self.view_date.year, self.view_date.month, day_num)
                                btn = DayButton(day_num, classes="day")
                                if day == self.from_date:
                                    btn.add_class("selected-from")
                                if day == self.until_date:
                                    btn.add_class("selected-until")
                                if (
                                    self.from_date
                                    and self.until_date
                                    and self.from_date < day < self.until_date
                                ):
                                    btn.add_class("selected-range")
                                yield btn

            with Horizontal(id="select-mode"):
                mode_from_variant = "primary" if self._date_mode == "from" else "default"
                mode_until_variant = "primary" if self._date_mode == "until" else "default"
                yield Button("Set From Date", id="mode-from", variant=mode_from_variant)
                yield Button("Set Until Date", id="mode-until", variant=mode_until_variant)

            with Horizontal(classes="center-row"):
                yield Button("Load Branches", variant="primary", id="load-btn")
            yield Static(id="error-msg")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "cal-prev":
            self.view_date = (self.view_date.replace(day=1) - timedelta(days=1)).replace(day=1)
            await self.recompose()
        elif btn_id == "cal-next":
            self.view_date = (self.view_date.replace(day=28) + timedelta(days=7)).replace(day=1)
            await self.recompose()
        elif btn_id == "mode-from":
            self._date_mode = "from"
            await self.recompose()
        elif btn_id == "mode-until":
            self._date_mode = "until"
            await self.recompose()
        elif btn_id == "load-btn":
            await self._load_branches()
        elif isinstance(event.button, DayButton):
            day_num = event.button.day_num
            selected = date(
                self.view_date.year, self.view_date.month, day_num
            )
            if self._date_mode == "from":
                self.from_date = selected
                self._date_mode = "until"
                if self.until_date and self.from_date > self.until_date:
                    self.from_date, self.until_date = (
                        self.until_date,
                        self.from_date,
                    )
            else:
                self.until_date = selected
                if self.from_date and self.until_date < self.from_date:
                    self.from_date, self.until_date = (
                        self.until_date,
                        self.from_date,
                    )
            await self.recompose()

    async def _load_branches(self) -> None:
        error_msg = self.query_one("#error-msg", Static)

        if not self.from_date or not self.until_date:
            error_msg.update("Please select both From and Until dates.")
            return
        if self.from_date > self.until_date:
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
                since=self.from_date,
                until=self.until_date,
            )
        )


class ConfirmationDialog(ModalScreen[bool]):
    """Modal dialog to confirm branch deletion."""

    def __init__(self, branches: list[str]) -> None:
        self.branches = branches
        super().__init__()

    def compose(self) -> ComposeResult:
        branch_list = "\n".join(f"  • {b}" for b in self.branches)
        yield Vertical(
            Label(f"Delete {len(self.branches)} branch(es)?"),
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
        self.branches: list[BranchInfo] = []
        self.selected: set[str] = set()
        super().__init__()

    def compose(self) -> ComposeResult:
        range_label = (
            f"From: {self.since or 'any'}  To: {self.until or 'any'}"
        )
        yield Header()
        yield Label(range_label, id="range-label")
        yield DataTable(id="branch-table")
        yield Static(id="status-bar")
        yield Footer()

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
            f"[P]rotected: {'show' if self.show_protected else 'hide'} | "
            f"[B]lacklisted: {'show' if self.show_blacklisted else 'hide'}"
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
        for b in self.branches:
            if not b.is_protected and not b.is_blacklisted:
                self.selected.add(b.name)
        self._refresh_table()

    def action_delete_selected(self) -> None:
        if not self.selected:
            return

        def handle_confirmation(confirmed: bool) -> None:
            if confirmed:
                to_delete = list(self.selected)
                failed = delete_branches(self.repo_path, to_delete)
                if failed:
                    self.query_one("#status-bar", Static).update(
                        f"Failed to delete: {', '.join(failed)}"
                    )
                else:
                    self.query_one("#status-bar", Static).update(
                        f"Deleted {len(to_delete)} branch(es)"
                    )
                self.selected.clear()
                self._load_branches()

        self.app.push_screen(
            ConfirmationDialog(list(self.selected)), handle_confirmation
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

    def on_mount(self) -> None:
        self.push_screen(CalendarScreen(self.repo_path))
