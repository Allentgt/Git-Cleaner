```text
      ▀   █               █
█▀▀█  █  ▀█▀  ▄▄▄▄  █▀▀▀  █  █▀▀█  ▀▀▀█  █▀▀█  █▀▀█  █▀▀▀
█▄▄█  █   █         █     █  █▀▀▀  █▀▀█  █  █  █▀▀▀  █
▄▄▄█  ▀   ▀         ▀▀▀▀  ▀  ▀▀▀▀  ▀▀▀▀  ▀  ▀  ▀▀▀▀  ▀
```

A **TUI tool** for interactively browsing and bulk-deleting git branches, plus **repo maintenance** (GC, repack, prune). Pick a date range, review branches with their last-commit dates, and delete locally and/or on remote — protected and blacklisted branches are automatically safeguarded.

Built with [Textual](https://textual.textualize.io/) and Python 3.11+.

![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)
![Textual](https://img.shields.io/badge/textual-8.x-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Installation

### With uv (recommended)

```bash
# Install as a global tool
uv tool install git-cleaner-tui

# Run in any git repo
git-cleaner-tui
```

### From source

```bash
git clone https://github.com/Allentgt/Git-Cleaner
cd git-cleaner
uv sync
uv run git-cleaner-tui --repo /path/to/repo
```

### Requirements

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A git repository

---

## Features

- **🗓️ Interactive calendar** — Pick From / Until dates visually, with highlighted range and auto-switching mode
- **🔍 Branch browser** — DataTable with multi-select, sorted by last commit date
- **🛡️ Protection** — `main`, `master`, `develop`, plus custom patterns from config; marked with 🔒, cannot be deleted
- **⛔ Blacklist** — Wildcard patterns (`archive/*`, `wip-*`); marked with ⛔, hidden by default
- **☁️ Remote deletion** — Toggle `r` to also delete branches on remote (`git push origin --delete`)
- **🔧 Maintenance dashboard** — Repo health stats, `git gc`, `git repack`, `git remote prune`, `git reflog expire`
- **📁 Configurable** — Per-repo `.git-branch-cleaner.toml` + global `~/.git-branch-cleaner.toml`
- **⚡ Fast** — Single `git for-each-ref` call for branch listing; bulk delete with one confirm

---

## Usage

### 0. Start the App

```bash
git-cleaner-tui
# or: git-cleaner-tui --repo /path/to/repo
```

Opens the calendar screen. Press **Maintenance** for repo optimization, or pick dates and **Load Branches** to clean.

### 1. Pick a Date Range

The app opens with an interactive calendar:

- **Navigate months** with `<` / `>` arrows
- **Set From date** — click a day (mode auto-switches to Until)
- **Set Until date** — click another day
- **Toggle mode** manually with `Set From Date` / `Set Until Date` buttons
- Selected range is highlighted in the calendar grid

When both dates are set, click **Load Branches**.

### 2. Browse and Select Branches

| Key | Action |
|-----|--------|
| `Space` | Toggle selection on focused row |
| `a` | Toggle select / deselect all selectable branches |
| `d` | Delete selected (with confirmation dialog) |
| `r` | Toggle remote deletion on/off |
| `p` | Toggle show/hide protected branches |
| `b` | Toggle show/hide blacklisted branches |
| `Escape` | Go back to calendar |
| `Ctrl+R` | Refresh branch list |

- **Protected** branches 🔒 are always safe — cannot be selected
- **Blacklisted** branches ⛔ are hidden by default; press `b` to review them
- Status bar shows: `Total | Selected | Protected | Blacklisted | Remote ON/OFF`

### 3. Confirm Deletion

A modal dialog lists all branches marked for deletion and shows the scope:

- **Local only** — `git branch -D <name>`
- **Local + remote** — `git branch -D <name>` then `git push origin --delete <name>`

Remote deletion is attempted only for branches that succeeded locally.

### 4. Maintenance Dashboard

Press **Maintenance** on the calendar screen opens a dashboard with:

**Repository Health:**
- `.git` directory size
- Loose object count (unpacked)
- Packed object count + total pack size
- Garbage objects
- Prune-packable objects

**Maintenance Tasks** (click any to run):

| Button | Command | Use Case |
|--------|---------|---------|
| **Git GC** | `git gc` | Standard housekeeping — compress revisions, remove loose objects |
| **GC Aggressive** | `git gc --aggressive` | Deep optimization (slower, best for repos that haven't been GC'd in months) |
| **Repack** | `git repack -Ad` | Reorganize pack files for better delta compression |
| **Prune Remote** | `git remote prune origin` | Remove stale remote-tracking refs (branches deleted on remote) |
| **Expire Reflog** | `git reflog expire --expire=90.days.ago` | Trim old reflog entries |
| **Run All** | Runs the 4 tasks above sequentially | One-shot full cleanup |

Tasks run asynchronously (UI stays responsive). Health stats refresh automatically after each task.

| Key | Action |
|-----|--------|
| `Escape` | Back to calendar |
| `r` | Refresh health stats |

---

## Configuration

### Project-level config

Place `.git-branch-cleaner.toml` in your repository root:

```toml
[protected]
patterns = ["release/*", "hotfix/*"]

[blacklist]
patterns = ["archive/*", "wip-*", "experiments/**"]
```

### Global config

Place `~/.git-branch-cleaner.toml` for user-wide rules:

```toml
[protected]
patterns = ["personal/*"]

[blacklist]
patterns = ["deps/*"]
```

### Merging strategy

All sources merged (hardcoded defaults → global → project), with project config taking highest precedence.

**Hardcoded defaults** (always active): `main`, `master`, `develop` are protected. The current checked-out branch is also automatically protected.

---

## Keybindings Reference

### Calendar Screen

| Key | Action |
|-----|--------|
| Click day | Select date (From or Until per mode) |
| Click `<` `>` | Navigate months |
| Click mode buttons | Toggle between From / Until selection |
| Click **Load Branches** | Proceed to branch list |
| Click **Maintenance** | Open maintenance dashboard |

### Branch List Screen

| Key | Action |
|-----|--------|
| `Space` | Toggle row selection |
| `a` | Toggle select / deselect all eligible |
| `d` | Delete selected |
| `r` | Toggle remote deletion |
| `p` | Toggle protected visibility |
| `b` | Toggle blacklisted visibility |
| `Escape` | Back to calendar |
| `Ctrl+R` | Refresh |

### Maintenance Screen

| Key | Action |
|-----|--------|
| `Escape` | Back to calendar |
| `r` | Refresh health stats |

---

## Project Structure

```
git-cleaner/
├── pyproject.toml           # Project metadata, deps, entry point
├── README.md
├── src/
│   └── git_cleaner/
│       ├── __init__.py
│       ├── __main__.py      # python -m git_cleaner entry
│       ├── cli.py           # CLI arg parsing
│       ├── app.py           # Textual TUI (Calendar, Maintenance, BranchList, Confirm)
│       ├── config.py        # TOML config loading and merging
│       └── git_ops.py       # Git subprocess wrapper (list, delete, gc, repack, etc.)
├── tests/
│   ├── test_config.py       # 7 tests
│   └── test_git_ops.py      # 16 tests
└── uv.lock
```

### Module responsibilities

| Module | Role |
|--------|------|
| `cli.py` | Parse `--repo` flag, launch the TUI app |
| `app.py` | Textual screens: calendar, maintenance dashboard, branch list with DataTable, confirmation dialog |
| `config.py` | Load `.git-branch-cleaner.toml` (project + global), fnmatch pattern matching |
| `git_ops.py` | `list_branches()`, `delete_branches()`, `delete_remote_branches()`, `get_repo_root()`, `get_git_dir_size()`, `get_object_stats()`, `run_gc()`, `repack_objects()`, `prune_remote()`, `expire_reflog()` |

---

## Development

```bash
# Set up
git clone https://github.com/Allentgt/Git-Cleaner
cd git-cleaner
uv sync --dev

# Run tests (23 total)
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test
uv run pytest tests/test_config.py -v

# Run the app
uv run git-cleaner-tui --repo /path/to/repo
```

### Test coverage

23 tests covering:

- Config loading and merging (defaults, project, global)
- Pattern matching (exact, wildcard, fnmatch)
- Git operations (listing, current branch detection, date filtering, deletion, remote deletion)
- Repository health (`get_git_dir_size`, `get_object_stats`)
- Maintenance tasks (`run_gc`, `repack_objects`, `prune_remote`, `expire_reflog`)
- Error handling (non-repo path, no remote configured, timeout)

---

## FAQ

**Q: Can I undo a deletion?**  
No — `git branch -D` is irreversible. Use the confirmation dialog to review before confirming.

**Q: Does it work on Windows?**  
Yes. Tested on Windows (PowerShell), macOS, and Linux. Requires Python 3.11+.

**Q: Can I delete remote branches?**  
Yes. Press `r` to toggle remote deletion on, then delete normally. Branches are deleted locally first, then via `git push origin --delete`.

**Q: How are dates filtered?**  
By the commit date of the branch tip (most recent commit). Both From and Until are inclusive.

**Q: Is `git gc --aggressive` safe?**  
Yes. It's more CPU-intensive than standard `git gc` but performs deeper optimization. Good for repos that haven't been GC'd in months. The UI won't freeze — it runs in a background thread.

**Q: Does the maintenance dashboard modify my repo?**  
Yes, the maintenance tasks run real git commands (`git gc`, `git repack`, etc.) that modify the `.git` directory. They are safe read-only operations that don't change working tree files.

---

## License

MIT
