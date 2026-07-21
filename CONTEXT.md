# Git Cleaner

A TUI tool for browsing and bulk-deleting git branches, with additional features for repository maintenance including stash management, worktree operations, commit analysis, and history rewriting.

## Language

### Branch Management

**Branch**:
A movable pointer to a commit in git. The primary entity managed by this tool.
_Avoid_: Ref, pointer

**Protected branch**:
A branch matching a pattern that cannot be deleted through the tool. Prevents accidental deletion of important branches like `main` or `release/*`.
_Avoid_: Safe branch, locked branch

**Blacklisted branch**:
A branch matching a pattern that is hidden from the default view but can be revealed with a toggle. Used for branches the user knows about but doesn't want to see regularly.
_Avoid_: Hidden branch, filtered branch

**Stale branch**:
A branch whose last commit is older than a configurable threshold, or a branch that exists locally but has been deleted on the remote.
_Avoid_: Old branch, inactive branch, orphan branch

### History Rewriting

**History rewrite**:
Modifying existing git commits to remove files or drop commits entirely, changing commit SHAs for the affected branch. Uses `git filter-repo`.
_Avoid_: Rewind, rollback, time travel

**File deletion from history**:
A history rewrite that removes a specific file from every commit in the branch, as if the file never existed.
_Avoid_: Remove file, delete file, untrack

**Commit drop**:
A history rewrite that removes a specific commit from the branch, rebasing all subsequent commits to fill the gap.
_Avoid_: Delete commit, remove commit, revert commit (revert is a different operation — it creates a new commit that undoes changes without rewriting history)

**Backup branch**:
An auto-created branch (named `backup/rewrite-{date}`) that captures the branch state before a history rewrite, enabling recovery via `git reset --hard`.
_Afloat_: Safety branch, recovery branch

### Repository Operations

**Worktree**:
A working directory associated with a branch, allowing multiple branches to be checked out simultaneously in separate directories.
_Avoid_: Working copy, workspace

**Stash**:
A temporary storage area for uncommitted changes, allowing the working directory to be cleaned without committing.
_Avoid_: Save, park

**Maintenance**:
Git housekeeping operations (GC, repack, prune, reflog expire) that optimize repository performance and reduce disk usage.
_Avoid_: Cleanup, garbage collection (too narrow — maintenance includes more than GC)

### UI Concepts

**Tab**:
A top-level section of the TUI, accessible via the tab bar. Each tab focuses on a specific domain (Branches, Commits, Stashes, etc.).
_Avoid_: Screen, page, panel

**Mode selector**:
A widget that switches between Local, Remote, and All branch views, controlling which refspecs are queried.
_Avoid_: Filter, toggle, scope
