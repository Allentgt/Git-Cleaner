# git-cleaner

A **TUI tool** for interactively browsing and bulk-deleting git branches. Pick a date range, review branches with their last-commit dates, and delete with confidence — protected and blacklisted branches are automatically safeguarded.

Built with [Textual](https://textual.textualize.io/) and Python 3.11+.

![GitHub](https://img.shields.io/badge/python-3.11+-blue?logo=python)
![GitHub](https://img.shields.io/badge/textual-8.x-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **🗓️ Interactive calendar** — Pick From / Until dates visually, with highlighted range and auto-switching mode
- **🔍 Branch browser** — DataTable with multi-select, sorted by last commit date
- **🛡️ Protection** — `main`, `master`, `develop`, plus custom patterns from config; marked with 🔒, cannot be deleted
- **⛔ Blacklist** — Wildcard patterns (`archive/*`, `wip-*`); marked with ⛔, hidden by default
- **📁 Configurable** — Per-repo `.git-branch-cleaner.toml` + global `~/.git-branch-cleaner.toml`
- **⚡ Fast** — Single `git for-each-ref` call for branch listing; bulk delete with one confirm

---

## Quick Start

```bash
# Install
uv tool install git-cleaner

# Or run directly from source
cd your-git-repo
uv run git-cleaner

# Or with explicit repo path
uv run git-cleaner --repo /path/to/repo
```

### Requirements

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A git repository

---

## Usage

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
| `a` | Select all visible unprotected, unblacklisted branches |
| `d` | Delete selected (with confirmation dialog) |
| `p` | Toggle show/hide protected branches |
| `b` | Toggle show/hide blacklisted branches |
| `Escape` | Go back to calendar |
| `Ctrl+R` | Refresh branch list |

- **Protected** branches 🔒 are always safe — cannot be selected
- **Blacklisted** branches ⛔ are hidden by default; press `b` to review them
- Status bar shows: `Total | Selected | Protected | Blacklisted`

### 3. Confirm Deletion

A modal dialog lists all branches marked for deletion. Confirm to delete with `git branch -D`.

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

## Installation

### With uv (recommended)

```bash
# Install as a global tool
uv tool install git-cleaner

# Run in any git repo
git-cleaner
```

### With pip

```bash
pip install git-cleaner
```

### From source

```bash
git clone https://github.com/your-org/git-cleaner
cd git-cleaner
uv sync          # creates venv and installs dependencies
uv run git-cleaner --repo /path/to/repo
```

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
│       ├── app.py           # Textual TUI (CalendarScreen, BranchListScreen, GitCleanerApp)
│       ├── config.py        # TOML config loading and merging
│       └── git_ops.py       # Git subprocess wrapper (list, delete branches)
├── tests/
│   ├── test_config.py       # 7 tests
│   └── test_git_ops.py      # 8 tests
└── uv.lock
```

### Module responsibilities

| Module | Role |
|--------|------|
| `cli.py` | Parse `--repo` flag, launch the TUI app |
| `app.py` | Textual screens: calendar date picker, branch list with DataTable, confirmation dialog |
| `config.py` | Load `.git-branch-cleaner.toml` (project + global), fnmatch pattern matching |
| `git_ops.py` | `list_branches()` via `git for-each-ref`, `delete_branches()`, `get_repo_root()` |

---

## Development

```bash
# Set up
git clone https://github.com/your-org/git-cleaner
cd git-cleaner
uv sync --dev

# Run tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test
uv run pytest tests/test_config.py -v

# Run the app
uv run git-cleaner --repo /path/to/repo
```

### Tests

15 tests covering:

- Config loading and merging (defaults, project, global)
- Pattern matching (exact, wildcard, fnmatch)
- Git operations (listing, current branch detection, date filtering, deletion)
- BranchInfo dataclass

---

## Keybindings Reference

### Calendar Screen

| Key | Action |
|-----|--------|
| Click day | Select date (From or Until per mode) |
| Click `<` `>` | Navigate months |
| Click mode buttons | Toggle between From / Until selection |
| Click **Load Branches** | Proceed to branch list |

### Branch List Screen

| Key | Action |
|-----|--------|
| `Space` | Toggle row selection |
| `a` | Select all eligible |
| `d` | Delete selected |
| `p` | Toggle protected visibility |
| `b` | Toggle blacklisted visibility |
| `Escape` | Back to calendar |
| `Ctrl+R` | Refresh |

---

## FAQ

**Q: Can I undo a deletion?**  
No — `git branch -D` is irreversible. Use the confirmation dialog to review before confirming.

**Q: Does it work on Windows?**  
Yes. Tested on Windows (PowerShell), macOS, and Linux. Requires Python 3.11+.

**Q: Can I delete remote branches?**  
No. Only local branches are listed and deleted. Use `git push origin --delete <branch>` for remote branches.

**Q: How are dates filtered?**  
By the commit date of the branch tip (most recent commit). Both From and Until are inclusive.

---

## License

MIT
