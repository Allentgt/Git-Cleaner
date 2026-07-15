# Phase 3: Dev Workflow Integration — Plan

## Goal
Add Commit Analysis and PR/MR Integration (GitHub + GitLab) to help users make informed decisions about branch cleanup.

## Scope (scoped from roadmap)
### In scope
1. **Commit Analysis** — git-native, no API needed
2. **PR/MR Integration** — GitHub + GitLab API, env-var tokens only

### Out of scope (ponytail: not relevant to cleanup tool)
- CI/CD Status — too many providers, marginal cleanup value
- Merge Helpers — `git merge --no-commit --no-ff` already exists
- Rebase Support — not relevant to branch cleanup

## Sub-phase 3a: Commit Analysis

### Data models
```python
@dataclass
class CommitInfo:
    short_hash: str
    author: str
    date: datetime
    subject: str

@dataclass
class AuthorStats:
    author: str
    commits: int
    insertions: int
    deletions: int
    first_date: datetime
    last_date: datetime
```

### git_ops.py additions
- `get_commit_log(repo_path, ref, limit=50)` → `list[CommitInfo]`
  - Refactor `get_commits_between` to use shared parser internally
- `get_author_stats(repo_path, branch)` → `list[AuthorStats]`
  - Single subprocess: `git log --format='%aE|%aI' --shortstat` then aggregate in Python
- `get_large_commits(repo_path, ref, threshold=50)` → `list[CommitInfo]`
  - Commits with >threshold changed files (parsed from `--shortstat`)

### UI: CommitAnalysisContent widget (flat layout, no sub-tabs)
- Horizontal: Label("Branch:") + Select + Button("Load")
- Three DataTables stacked vertically, toggled with `.display`:
  - `#commit-log-table` — hash, author, date, subject (default visible)
  - `#commit-authors-table` — author, commits, insertions, deletions, first/last date (default hidden)
  - `#commit-hotspots-table` — hash, author, date, subject (default hidden)
- Button row: "Log" / "Authors" / "Hotspots" to toggle which DataTable is visible
- `#commit-status` — status label
- Wire into MainScreen as "Commits" tab

## Sub-phase 3b: PR/MR Integration (GitHub + GitLab)

### Provider detection
Auto-detect from git remote URL:
- `github.com` → GitHub provider
- `gitlab.` → GitLab provider (including self-hosted)
- No match → disable PR tab with message

### Auth (env vars only — no TOML token storage)
| Provider | Token env var | URL override |
|----------|--------------|-------------|
| GitHub   | `GITHUB_TOKEN` or `GH_TOKEN` | N/A |
| GitLab   | `GITLAB_TOKEN` or `GITLAB_PAT` | `GITLAB_URL` (default: `https://gitlab.com`) |

### git_ops.py additions
```python
@dataclass
class PRInfo:
    number: int          # MR !123 for GitLab
    title: str
    state: str           # open/closed/merged
    url: str
    author: str
    branch: str          # head branch
    mergeable: bool | None
```

- `_detect_provider(repo_path)` → `"github" | "gitlab" | None`
- `_get_api_token(provider)` → `str | None`
- `_get_api_repo(repo_path, provider)` → `str` (owner/repo or project path)
- `_api_get(repo_path, endpoint)` → `dict` — stdlib `urllib.request`, no new deps
- `list_open_prs(repo_path)` → `list[PRInfo]`
  - GitHub: `GET /repos/{owner}/{repo}/pulls?state=open`
  - GitLab: `GET /projects/{id}/merge_requests?state=opened`
- `get_pr_for_branch(repo_path, branch)` → `PRInfo | None`
  - GitHub: filter `list_open_prs` by head branch
  - GitLab: filter by source branch

### UI: PRIntegrationContent widget
- DataTable: branch, PR#, title, author, state
- Actions: "Open in browser" (launch browser to URL)
- `#pr-status` — status label
- If no token detected: show "Set GITHUB_TOKEN or GITLAB_TOKEN env var"
- Wire into MainScreen as "Pull Requests" tab

## Files to modify
- `src/git_cleaner/git_ops.py` — add CommitInfo, AuthorStats, PRInfo, all new functions
- `src/git_cleaner/app.py` — add CommitAnalysisContent, PRIntegrationContent, wire tabs, help overlay

## Implementation order
1. Commit Analysis (git-only, self-contained)
2. PR/MR Integration (multi-provider API)
