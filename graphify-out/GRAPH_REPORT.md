# Graph Report - F:\AI\git-cleaner  (2026-07-13)

## Corpus Check
- 19 files · ~220,029 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 392 nodes · 796 edges · 20 communities detected
- Extraction: 58% EXTRACTED · 42% INFERRED · 0% AMBIGUOUS · INFERRED: 338 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]

## God Nodes (most connected - your core abstractions)
1. `BranchInfo` - 110 edges
2. `BranchesContent` - 72 edges
3. `StashInfo` - 64 edges
4. `MainScreen` - 31 edges
5. `MaintenanceContent` - 21 edges
6. `UndoHistory` - 17 edges
7. `_init_git_repo()` - 16 edges
8. `HelpOverlay` - 14 edges
9. `list_branches()` - 13 edges
10. `StashContent` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Initialize a git repo and create branches with the given names.` --uses--> `BranchesContent`  [INFERRED]
  F:\AI\git-cleaner\tests\test_regex_search.py → F:\AI\git-cleaner\src\git_cleaner\app.py
- `Regex pattern is compiled correctly via the actual code path.` --uses--> `BranchesContent`  [INFERRED]
  F:\AI\git-cleaner\tests\test_regex_search.py → F:\AI\git-cleaner\src\git_cleaner\app.py
- `Empty search returns None (no filtering).` --uses--> `BranchesContent`  [INFERRED]
  F:\AI\git-cleaner\tests\test_regex_search.py → F:\AI\git-cleaner\src\git_cleaner\app.py
- `Invalid regex falls back to literal matching via the actual code path.` --uses--> `BranchesContent`  [INFERRED]
  F:\AI\git-cleaner\tests\test_regex_search.py → F:\AI\git-cleaner\src\git_cleaner\app.py
- `Compiled pattern is case-insensitive.` --uses--> `BranchesContent`  [INFERRED]
  F:\AI\git-cleaner\tests\test_regex_search.py → F:\AI\git-cleaner\src\git_cleaner\app.py

## Hyperedges (group relationships)
- **Git Cleaner Core Architecture** — config_module, git_ops_module, tui_app, cli_entry_point [EXTRACTED 0.90]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (71): _get_health_indicator(), Maintenance tab: health display and git maintenance tasks., Stashes tab: list stashes with drop/apply/pop actions., Single screen with tabbed content: Branches, Maintenance, Stashes., Stashes tab: list stashes with drop/apply/pop actions., Modal dialog to confirm branch deletion., Modal to manage bookmarked repos and switch between them., Single screen with tabbed content: Branches, Maintenance, Stashes. (+63 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (54): apply_stash(), delete_branches(), delete_remote_branches(), expire_reflog(), get_branch_details(), get_git_dir_size(), get_object_stats(), get_repo_root() (+46 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (25): _format_key(), HelpOverlay, MainScreen, UndoHistory, Screen, compose() iterates MainScreen.BINDINGS; changing them doesn't crash., on_key must dismiss the overlay., _format_key wraps the key in brackets. (+17 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (17): BranchesContent, Restore a deleted branch via ``git branch <name> <commit>``., restore_branch(), Tests for batch delete progress indicator., Progress message formats as 'Deleting N/M: branch-name'., handle_confirmation must be async to yield to the event loop., _on_delete_progress accepts (current, total, branch)., test_handle_confirmation_is_async() (+9 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (6): ConfirmationDialog, MaintenanceContent, RepoFooter, StashContent, Footer, Vertical

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (27): RepoSwitcher, add_bookmark(), get_blacklist_patterns(), get_protected_patterns(), load_bookmarks(), load_theme(), _load_toml(), matches_any() (+19 more)

### Community 6 - "Community 6"
Cohesion: 0.13
Nodes (14): _age_from(), _get_status_badge(), _is_stale(), _on_filter_changed(), _on_search_changed(), _upstream_str(), Blacklisted branch gets 'blacklisted' badge., Branch with multiple classifications gets combined badge. (+6 more)

### Community 7 - "Community 7"
Cohesion: 0.16
Nodes (19): _compile_search(), _init_git_repo(), Branch with a dash-only name is matched by a plain-literal search., Regex pattern is compiled correctly via the actual code path., Empty search returns None (no filtering)., Invalid regex falls back to literal matching via the actual code path., Compiled pattern is case-insensitive., Regex pattern filters real branches from a real git repo. (+11 more)

### Community 8 - "Community 8"
Cohesion: 0.14
Nodes (17): Blacklisted Branch Patterns, Branch Browser Feature, Branch Deletion Undo, BranchInfo Dataclass, CLI Entry Point (cli.py), Config Module (config.py), CSV/JSON Export, Date Range Filtering (+9 more)

### Community 9 - "Community 9"
Cohesion: 0.17
Nodes (15): _is_within_age_limit(), Branch committed exactly 30 days ago is within a 30-day limit (<=)., Branch committed 31 days ago is excluded by a 30-day limit., None max_age_days means no filtering., Zero max_age_days means no filtering (matches blank select)., Filtering a list of branches keeps only those within the age limit., With no filter, all branches are included., Branch committed 10 days ago is within a 30-day limit. (+7 more)

### Community 10 - "Community 10"
Cohesion: 0.23
Nodes (11): _get_staleness_color(), Test that medium-age branches get yellow color., Test that old branches get red color., Test that exactly 30 days is yellow (boundary, < 30 is green)., Test that exactly 90 days is red (boundary, < 90 is yellow)., Test that recent branches get green color., test_exactly_30_days_is_yellow(), test_exactly_90_days_is_red() (+3 more)

### Community 11 - "Community 11"
Cohesion: 0.25
Nodes (5): App, GitCleanerApp, main(), Persist the theme name to the global config file., save_theme()

### Community 12 - "Community 12"
Cohesion: 0.5
Nodes (4): _init_repo(), select_by_author should not select protected or blacklisted branches., Initialize a git repo with branches by different authors., test_select_by_author_filters_protected_and_blacklisted()

### Community 13 - "Community 13"
Cohesion: 0.5
Nodes (4): AGENTS.md - Agent Instructions, README.md - Project Documentation, Git Cleaner TUI Project, Git Cleaner Logo

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (1): Maintenance Dashboard Feature

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (1): Stash Browser Feature

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (1): Multi-Repo Bookmarks Feature

## Knowledge Gaps
- **43 isolated node(s):** `Return merged list of protected branch patterns.      Order of precedence (last`, `Return merged list of blacklist patterns from global + project config.`, `Check if a branch name matches any of the given fnmatch patterns.`, `Return the saved theme name, or the default.`, `Persist the theme name to the global config file.` (+38 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 14`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `__main__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `Maintenance Dashboard Feature`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `Stash Browser Feature`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `Multi-Repo Bookmarks Feature`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BranchInfo` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 9`, `Community 10`, `Community 11`, `Community 12`?**
  _High betweenness centrality (0.380) - this node is a cross-community bridge._
- **Why does `BranchesContent` connect `Community 3` to `Community 0`, `Community 4`, `Community 6`, `Community 7`, `Community 9`, `Community 10`?**
  _High betweenness centrality (0.250) - this node is a cross-community bridge._
- **Why does `StashInfo` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 11`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Are the 108 inferred relationships involving `BranchInfo` (e.g. with `RepoFooter` and `BranchesContent`) actually correct?**
  _`BranchInfo` has 108 INFERRED edges - model-reasoned connections that need verification._
- **Are the 43 inferred relationships involving `BranchesContent` (e.g. with `BranchInfo` and `StashInfo`) actually correct?**
  _`BranchesContent` has 43 INFERRED edges - model-reasoned connections that need verification._
- **Are the 62 inferred relationships involving `StashInfo` (e.g. with `RepoFooter` and `BranchesContent`) actually correct?**
  _`StashInfo` has 62 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `MainScreen` (e.g. with `BranchInfo` and `StashInfo`) actually correct?**
  _`MainScreen` has 12 INFERRED edges - model-reasoned connections that need verification._