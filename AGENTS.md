# AGENTS.md — Git Cleaner (git-cleaner-tui)

## Quick start

```bash
uv sync --dev
uv run git-cleaner-tui           # CWD must be a git repo
uv run git-cleaner-tui --repo /path
uv run pytest                     # 23 tests, <10s
```

## Package structure

```
src/git_cleaner/
├── cli.py       # entrypoint: git_cleaner.cli:main (lazy-imports app.py)
├── app.py       # Textual App (~1450 lines), all screens/widgets in one file
├── git_ops.py   # BranchInfo/StashInfo dataclasses, git subprocess wrappers
├── config.py    # TOML config: protected, blacklist, theme, bookmarks
└── __main__.py  # python -m git_cleaner support
```

- Build: `hatchling`, no extra config
- Dependencies: `textual`, `textual-timepiece`, `whenever`
- Dev dependencies: `pytest` only — no linter, no typechecker, no formatter config in repo

## Config

`~/.git-branch-cleaner.toml` (global) and/or repo `.git-branch-cleaner.toml`:

```toml
[protected]
patterns = ["release/*", "hotfix/*"]

[blacklist]
patterns = ["archive/*"]

[theme]
name = "textual-dark"

[bookmarks]
paths = ['C:\\path\\to\\repo']
```

**Gotcha:** `save_bookmarks()` writes TOML with **single-quoted literal strings** — critical for Windows backslash paths. Double-quoted strings would corrupt the config (backslashes escape). If editing `config.py`, preserve single-quote output in `save_bookmarks()`.

## Tests

- Tests create **real git repos** in `tempfile.TemporaryDirectory` — no mocks, slow but thorough
- `test_git_ops.py` uses `_init_git_repo()` helper that calls `git init -b main`, adds commits, creates branches
- No test markers, no conftest, no fixtures
- Single command: `uv run pytest`

## Key conventions

- All TUI screens/widgets live in one file (`app.py`). Adding a new content screen means adding a new class there.
- CSS is embedded as a module-level string in `app.py` (not separate `.tcss` files).
- Git operations use `subprocess.run` with `capture_output=True`, never `gitpython`.
- `BranchInfo` dataclass has optional fields: `author`, `ahead`, `behind`, `has_upstream`, `commit_hash`, `is_protected`, `is_blacklisted`.
- `list_branches()` uses a single `git for-each-ref` call with `--format` — the core perf trick.
- Version lives only in `pyproject.toml`. Bump there, build with `uv build`, publish with `twine upload dist/*`.

## Publishing

```bash
uv build
twine upload dist/*
```

Auth uses `~/.pypirc` (not env vars):

```ini
[distutils]
index-servers =
    pypi

[pypi]
username = __token__
password = pypi-...
```

GitHub releases are automated via `.github/workflows/release.yml` — push a tag (`git tag v1.2.0 && git push origin v1.2.0`) to create a release with sdist/wheel attached.

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
