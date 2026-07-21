<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="Git Cleaner — TUI for managing and cleaning up git repositories">
</p>

<h3 align="center">Interactively browse, filter, and bulk-delete git branches from a fast terminal UI.</h3>

<p align="center">
  <a href="https://pypi.org/project/git-cleaner-tui/"><img src="https://img.shields.io/pypi/v/git-cleaner-tui?color=238636&label=PyPI" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/python-3.11+-3776ab?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/textual-8.x-ef8340?logo=terminal&logoColor=white" alt="Textual 8.x">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
</p>

---

## Install

```bash
uv tool install git-cleaner-tui
git-cleaner
```

Or from source:

```bash
git clone https://github.com/Allentgt/Git-Cleaner
cd git-cleaner
uv sync
uv run git-cleaner --repo /path/to/repo
```

Requires Python ≥ 3.11, [uv](https://docs.astral.sh/uv/) (or pip), and a git repository.

Optional: `pip install git-filter-repo` for history rewriting features (delete files from history, drop commits).

---

## Features

### Branches tab
| | Feature | Details |
|---|---------|---------|
| 🌳 | **Tree view** | Branches grouped by prefix (`feature/auth/login` → `feature` → `auth` → `login`) |
| 🌐 | **Local / Remote / All** | Press `r` to cycle scope; All mode shows branches under `Local (N)` and `Remote (N)` headings |
| 📅 | **Date filtering** | Calendar picker or presets: 7d, 30d, 90d, 1y |
| 🛡️ | **Protection** | `main`/`master`/`develop` + custom patterns; cannot be selected |
| ⛔ | **Blacklist** | Wildcard patterns (`archive/*`); hidden by default |
| ☁️ | **Remote deletion** | Remote branches detected and pushed to `git push origin --delete` |
| 🧪 | **Dry run** | Preview deletions without executing |
| ↩️ | **Undo** | Press `u` to restore the last batch via reflog |
| 📥 | **Export** | Download filtered branch list as CSV or JSON |

### Commits tab
| | Feature | Details |
|---|---------|---------|
| 📋 | **Commit log** | Load and browse commits for any branch |
| 🗑️ | **Delete file from history** | Press `f` to remove a file from every commit using `git filter-repo` |
| ✂️ | **Drop commit** | Press `x` to remove a commit and rewrite all subsequent commits |
| 🚀 | **Force push** | After rewrite, prompted to force-push to origin (creates backup branch first) |

### Compare, Worktrees, Pull Requests, Stale
| | Feature | Details |
|---|---------|---------|
| 🔀 | **Branch compare** | Compare any two branches side by side |
| 🌲 | **Worktrees** | List, create, and remove git worktrees |
| 🔗 | **Pull Requests** | View open PRs/MRs from GitHub or GitLab |
| 🧊 | **Stale detection** | Identify branches with no recent activity |

### Other
| | Feature | Details |
|---|---------|---------|
| 🔧 | **Maintenance** | GC, Repack, Prune, Reflog expiry — one click |
| 📦 | **Stash browser** | List, drop, apply, pop stashes |
| 🔖 | **Bookmarks** | `Ctrl+B` to save and switch between repos |
| ⚡ | **Fast** | Single `git for-each-ref` call; bulk delete with one confirm |

---

## Keybindings

| Key | Action |
|-----|--------|
| `Space` | Toggle branch selection |
| `a` | Select / deselect all |
| `d` | Delete selected (with confirmation) |
| `r` | Cycle branch scope (Local → Remote → All) |
| `p` | Toggle protected visibility |
| `b` | Toggle blacklisted visibility |
| `u` | Undo last deletion batch |
| `U` | Undo all deletions |
| `H` | Undo history |
| `f` | Delete file from history *(Commits tab)* |
| `x` | Drop commit from history *(Commits tab)* |
| `Ctrl+R` | Refresh |
| `Ctrl+B` | Open bookmarks |
| `h` / `?` | Help |

---

## Configuration

`~/.git-branch-cleaner.toml` (global) or `.git-branch-cleaner.toml` (per-repo):

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

## Development

```bash
git clone https://github.com/Allentgt/Git-Cleaner
cd git-cleaner
uv sync --dev
uv run pytest
uv run git-cleaner-tui
```

---

## FAQ

<details>
<summary><b>Can I undo a deletion?</b></summary>

Yes — press <code>u</code> immediately after deleting. Undo uses <code>git branch &lt;name&gt; &lt;hash&gt;</code> via the stored commit hash.
</details>

<details>
<summary><b>Does it work on Windows?</b></summary>

Yes. Tested on Windows, macOS, and Linux. Python 3.11+.
</details>

<details>
<summary><b>How are dates filtered?</b></summary>

By the commit date of the branch tip. Both From and Until are inclusive.
</details>

<details>
<summary><b>Does the maintenance dashboard modify my repo?</b></summary>

It runs real git commands that modify <code>.git</code>. They don't change working tree files.
</details>

---

## License

MIT
