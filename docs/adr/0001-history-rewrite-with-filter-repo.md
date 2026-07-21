# Use git-filter-repo for history rewriting

Git Cleaner is adding history rewriting features: deleting files from entire commit history and dropping commits. We decided to use `git-filter-repo` as the sole implementation tool, bundled as a PyPI dependency.

`git filter-branch` is officially deprecated, slow, and has known bugs. `git filter-repo` is the modern replacement — faster, safer, and actively maintained. The alternative (BFG Repo Cleaner) is Java-based and adds a JVM dependency for no benefit over filter-repo.

Adding `git-filter-repo` to `pyproject.toml` dependencies means it's always available when the tool is installed — no runtime detection, no "install this" messages, no greyed-out features. The trade-off is a slightly larger install footprint, but filter-repo is pure Python with minimal dependencies.

History rewriting is scoped to the current branch only. Rewriting all branches simultaneously is a footgun — it creates inconsistent states when branches diverge. The tool auto-creates a backup branch before any rewrite and prints the restore command on success, but does not force-push — the user decides when to coordinate with their team.
