![Git Cleaner](logo/git-cleaner.png)

TUI tool for interactively browsing and bulk-deleting git branches, with repo maintenance (GC, repack, prune), a stash browser, and multi-repo bookmarks.

![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)
![Textual](https://img.shields.io/badge/textual-8.x-orange)
![License](https://img.shields.io/badge/license-MIT-green)

Built with [Textual](https://textual.textualize.io/) + Python 3.11+.

---

## Installation

```bash
uv tool install git-cleaner-tui
git-cleaner-tui
```

Or from source:

```bash
git clone https://github.com/Allentgt/Git-Cleaner
cd git-cleaner
uv sync
uv run git-cleaner-tui --repo /path/to/repo
```

Requires Python ≥ 3.11, uv (or pip), and a git repository.

---

## Features

- **🗓️ Date filtering** — Pick From/Until dates (calendar picker) or use presets: 7d, 30d, 90d, 1y
- **🔍 Branch browser** — Tree view with prefix grouping (`feature/`, `bugfix/`, …), ahead/behind tracking, stale badge (>180d), details pane on select
- **🛡️ Protection** — `main`/`master`/`develop` + custom patterns from `.git-branch-cleaner.toml`; cannot be selected
- **⛔ Blacklist** — Wildcard patterns (`archive/*`); hidden by default
- **☁️ Remote deletion** — Toggle `r` to also delete on remote (`git push origin --delete`)
- **🧪 Dry Run** — Toggle to preview deletions without executing
- **↩️ Undo** — Press `u` to restore the last batch via reflog (`git branch <name> <hash>`)
- **📥 CSV/JSON export** — Download filtered branch list to CWD
- **🔧 Maintenance dashboard** — Repo health stats + GC/Repack/Prune/Reflog tasks
- **📦 Stash browser** — List/drop/apply/pop stashes from the Stashes tab
- **🔖 Multi-repo bookmarks** — `Ctrl+B` to save and switch between repos
- **⚡ Fast** — Single `git for-each-ref` call; bulk delete with one confirm

---

## Usage

```bash
git-cleaner-tui
# or: git-cleaner-tui --repo /path/to/repo
```

### Branches Tab

| Key | Action |
|-----|--------|
| `Space` | Toggle selection |
| `a` | Select / deselect all |
| `d` | Delete selected (with confirmation) |
| `r` | Toggle remote deletion |
| `p` | Toggle protected visibility |
| `b` | Toggle blacklisted visibility |
| `u` | Undo last deletion batch |
| `Ctrl+R` | Refresh |
| `Ctrl+B` | Open bookmarks |

Date presets (7d/30d/90d/1y) sit next to the Load button. Branches appear grouped by prefix in a collapsible Tree. Select a leaf node to see its last-commit details.

### Maintenance Tab

Health stats and one‑click tasks: Git GC, GC Aggressive, Repack, Prune Remote, Expire Reflog, or Run All (sequential). Runs async — UI stays responsive.

### Stashes Tab

DataTable of all stashes with Drop / Apply / Pop / Refresh buttons.

### Bookmarks

`Ctrl+B` opens a modal to add the current repo, remove it, or switch to a bookmarked repo. Persisted in `~/.git-branch-cleaner.toml`.

---

## Configuration

`~/.git-branch-cleaner.toml` (global) or `.git-branch-cleaner.toml` (per‑repo):

```toml
[protected]
patterns = ["release/*", "hotfix/*"]

[blacklist]
patterns = ["archive/*", "wip-*"]

[theme]
name = "textual-dark"
```

Hardcoded defaults (always active): `main`, `master`, `develop`. The checked-out branch is also protected.

---

## Keybindings

| Tab | Key | Action |
|-----|-----|--------|
| Branches | `Space` | Toggle selection |
| Branches | `a` | Select / deselect all |
| Branches | `d` | Delete selected |
| Branches | `r` | Toggle remote |
| Branches | `p` | Toggle protected |
| Branches | `b` | Toggle blacklisted |
| Branches | `u` | Undo deletion |
| Branches | `Ctrl+R` | Reload |
| All | `Ctrl+B` | Bookmarks |

---

## Development

```bash
git clone https://github.com/Allentgt/Git-Cleaner
cd git-cleaner
uv sync --dev
uv run pytest        # 23 tests
uv run git-cleaner-tui
```

---

## FAQ

**Q: Can I undo a deletion?**  
Yes — press `u` immediately after deleting. Undo uses `git branch <name> <hash>` via the stored commit hash.

**Q: Does it work on Windows?**  
Yes. Tested on Windows, macOS, Linux. Python 3.11+.

**Q: How are dates filtered?**  
By the commit date of the branch tip. Both From and Until are inclusive.

**Q: Does the maintenance dashboard modify my repo?**  
It runs real git commands that modify `.git`. They don't change working tree files.

---

## License

MIT
