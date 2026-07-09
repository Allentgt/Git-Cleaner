import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class BranchInfo:
    name: str
    commit_date: datetime
    is_current: bool
    author: str = ""
    ahead: int = 0
    behind: int = 0
    has_upstream: bool = False
    commit_hash: str = ""
    is_protected: bool = False
    is_blacklisted: bool = False


def get_repo_root(path: Path) -> Path:
    """Find the git working tree root for a given path."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        cwd=path,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Not a git repository: {path}")
    return Path(result.stdout.strip()).resolve()


def list_branches(
    repo_path: Path,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[BranchInfo]:
    """List git branches with commit timestamps and HEAD marker.

    Uses a single git for-each-ref call for efficiency.
    Filters by committer date range if since/until are provided.
    """
    result = subprocess.run(
        [
            "git",
            "for-each-ref",
            "refs/heads/",
            "--format=%(refname:short)%00%(committerdate:unix)%00%(authorname)%00%(HEAD)%00%(upstream:short)%00%(upstream:track,nobracket)%00%(objectname)",
        ],
        capture_output=True,
        text=True,
        cwd=repo_path,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git error: {result.stderr}")

    branches: list[BranchInfo] = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\0")
        if len(parts) < 4:
            continue
        name = parts[0]
        ts = int(parts[1])
        author = parts[2]
        is_current = parts[3] == "*"
        upstream = parts[4] if len(parts) > 4 else ""
        track = parts[5] if len(parts) > 5 else ""
        commit_hash = parts[6] if len(parts) > 6 else ""
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)

        if since is not None and dt < since:
            continue
        if until is not None and dt > until:
            continue

        has_upstream = bool(upstream)
        ahead, behind = 0, 0
        if has_upstream and track:
            for part in track.split(", "):
                part = part.strip()
                if part.startswith("ahead "):
                    ahead = int(part[6:])
                elif part.startswith("behind "):
                    behind = int(part[7:])

        branches.append(
            BranchInfo(
                name=name, commit_date=dt, is_current=is_current, author=author,
                ahead=ahead, behind=behind, has_upstream=has_upstream,
                commit_hash=commit_hash,
            )
        )

    return branches


def delete_branches(repo_path: Path, names: list[str]) -> list[str]:
    """Delete local branches by name. Returns list of names that failed to delete."""
    failed: list[str] = []
    for name in names:
        result = subprocess.run(
            ["git", "branch", "-D", name],
            capture_output=True,
            text=True,
            cwd=repo_path,
        )
        if result.returncode != 0:
            failed.append(name)
    return failed


def delete_remote_branches(repo_path: Path, names: list[str]) -> list[str]:
    """Delete remote branches via git push origin --delete.

    Returns list of names that failed to delete.
    """
    repo_root = get_repo_root(repo_path)
    failed: list[str] = []
    for name in names:
        result = subprocess.run(
            ["git", "push", "origin", "--delete", name],
            capture_output=True,
            text=True,
            cwd=repo_root,
            timeout=30,
        )
        if result.returncode != 0:
            failed.append(name)
    return failed


def restore_branch(repo_path: Path, branch_name: str, commit_hash: str) -> tuple[bool, str]:
    """Restore a deleted branch via ``git branch <name> <commit>``."""
    result = subprocess.run(
        ["git", "branch", branch_name, commit_hash],
        capture_output=True, text=True, cwd=repo_path,
    )
    if result.returncode == 0:
        return True, f"Restored {branch_name}"
    return False, f"Failed to restore {branch_name}: {result.stderr.strip()}"


# ─── Stash operations ──────────────────────────────────────────────────


@dataclass
class StashInfo:
    ref: str         # stash@{0}
    branch: str      # extracted from reflog subject
    message: str     # stash description
    date: datetime


def _parse_stash_subject(subject: str) -> tuple[str, str]:
    """Parse reflog subject into (branch, message).

    Handles both 'On branchname: message' and 'WIP on branchname: message'.
    """
    for prefix in ("On ", "WIP on "):
        if subject.startswith(prefix):
            rest = subject[len(prefix):]
            colon = rest.find(": ")
            if colon > 0:
                return rest[:colon], rest[colon + 2:]
            return "", rest
    return "", subject


def list_stashes(repo_path: Path) -> list[StashInfo]:
    """Return list of stashes with metadata."""
    result = subprocess.run(
        ["git", "stash", "list", "--format=%gd||S||%gD||S||%gs||S||%ci"],
        capture_output=True, text=True, cwd=repo_path,
    )
    if result.returncode != 0:
        return []

    stashes: list[StashInfo] = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("||S||")
        if len(parts) < 4:
            continue
        ref = parts[0]
        subject = parts[2]
        date_str = parts[3].strip()
        branch, message = _parse_stash_subject(subject)
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z") if date_str else datetime.now(timezone.utc)
        stashes.append(StashInfo(ref=ref, branch=branch, message=message, date=dt))
    return stashes


def drop_stash(repo_path: Path, ref: str) -> tuple[bool, str]:
    """Drop a stash entry."""
    result = subprocess.run(
        ["git", "stash", "drop", ref],
        capture_output=True, text=True, cwd=repo_path,
    )
    return result.returncode == 0, result.stderr.strip() or f"Dropped {ref}"


def apply_stash(repo_path: Path, ref: str) -> tuple[bool, str]:
    """Apply a stash without removing it."""
    result = subprocess.run(
        ["git", "stash", "apply", ref],
        capture_output=True, text=True, cwd=repo_path,
    )
    return result.returncode == 0, result.stderr.strip() or f"Applied {ref}"


def pop_stash(repo_path: Path, ref: str) -> tuple[bool, str]:
    """Pop (apply + drop) a stash."""
    result = subprocess.run(
        ["git", "stash", "pop", ref],
        capture_output=True, text=True, cwd=repo_path,
    )
    return result.returncode == 0, result.stderr.strip() or f"Popped {ref}"


def get_branch_details(repo_path: Path, branch_name: str) -> str:
    """Return formatted last-commit details + diff stat for a branch."""
    try:
        result = subprocess.run(
            [
                "git", "show", "--stat", "-1",
                "--format=Commit: %H%nAuthor: %an <%ae>%nDate: %ai%n%n%s%n",
                branch_name,
            ],
            capture_output=True, text=True, cwd=repo_path, timeout=10,
        )
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Timed out fetching branch details"


# ─── Repository health & maintenance ─────────────────────────────────────────


def _human_size(bytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes //= 1024
    return f"{bytes:.1f} TB"


def get_git_dir_size(repo_path: Path) -> str:
    """Return human-readable total size of the .git directory."""
    git_dir = repo_path / ".git"
    if not git_dir.is_dir():
        raise RuntimeError(f"No .git directory found at {git_dir}")

    total = 0
    for dirpath, dirnames, filenames in os.walk(git_dir):
        for f in filenames:
            try:
                total += (Path(dirpath) / f).stat().st_size
            except OSError:
                pass
    return _human_size(total)


def get_object_stats(repo_path: Path) -> dict[str, str]:
    """Return parsed output of ``git count-objects -v`` as a dict."""
    result = subprocess.run(
        ["git", "count-objects", "-v"],
        capture_output=True,
        text=True,
        cwd=repo_path,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git count-objects failed: {result.stderr}")

    stats: dict[str, str] = {}
    for line in result.stdout.strip().splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            stats[key.strip()] = val.strip()
    return stats


def _run_cmd(
    cmd: list[str],
    cwd: Path,
    timeout: int,
    on_output: Callable[[str], None] | None = None,
) -> tuple[int, str]:
    """Run a command, optionally streaming stdout/stderr line by line.

    When *on_output* is provided, the command uses ``Popen`` so output flows
    to the callback in real time.  When *on_output* is ``None`` (default) it
    falls back to the simpler ``subprocess.run``.

    Returns ``(returncode, stderr_text)``.
    """
    stderr_lines: list[str] = []

    if on_output is None:
        # ── Non‑streaming (keeps existing behaviour) ────────────────────
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout
            )
            if result.stderr:
                stderr_lines.append(result.stderr.strip())
            return result.returncode, "\n".join(stderr_lines)
        except subprocess.TimeoutExpired:
            return -1, f"Command timed out after {timeout}s"

    # ── Streaming ──────────────────────────────────────────────────────
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=cwd,
        )
        for raw in iter(proc.stdout.readline, ""):  # type: ignore[union-attr]
            line = raw.rstrip("\n\r")
            if not line:
                continue
            stderr_lines.append(line)
            on_output(line)

        proc.wait(timeout=timeout)
        return proc.returncode, "\n".join(stderr_lines)

    except subprocess.TimeoutExpired:
        proc.kill()  # type: ignore[possibly-undefined]
        on_output("[red]Command timed out[/]")
        return -1, "Command timed out"
    except FileNotFoundError:
        on_output("[red]Git command not found[/]")
        return -1, "Git command not found"


def run_gc(
    repo_path: Path,
    aggressive: bool = False,
    timeout: int = 300,
    on_output: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """Run ``git gc`` (optionally ``--aggressive``).

    When *on_output* is provided, stdout/stderr is streamed line by line.

    Returns ``(success, message)``.
    """
    cmd = ["git", "gc"]
    if aggressive:
        cmd.append("--aggressive")
    rc, stderr = _run_cmd(cmd, repo_path, timeout, on_output=on_output)
    if rc == 0:
        label = "GC (aggressive)" if aggressive else "GC"
        return True, f"{label} completed"
    return False, stderr.strip() if stderr else "GC failed"


def repack_objects(
    repo_path: Path,
    timeout: int = 300,
    on_output: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """Run ``git repack -Ad`` to optimize pack files."""
    rc, stderr = _run_cmd(
        ["git", "repack", "-Ad"], repo_path, timeout, on_output=on_output
    )
    if rc == 0:
        return True, "Repack completed"
    return False, stderr.strip() if stderr else "Repack failed"


def prune_remote(
    repo_path: Path,
    remote: str = "origin",
    timeout: int = 30,
    on_output: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """Run ``git remote prune <remote>`` to clean stale remote-tracking refs."""
    rc, stderr = _run_cmd(
        ["git", "remote", "prune", remote], repo_path, timeout, on_output=on_output
    )
    if rc == 0:
        return True, f"Remote '{remote}' pruned"
    return False, stderr.strip() if stderr else "Prune failed"


def expire_reflog(
    repo_path: Path,
    days: int = 90,
    timeout: int = 60,
    on_output: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """Expire reflog entries older than *days* days."""
    rc, stderr = _run_cmd(
        ["git", "reflog", "expire", f"--expire={days}.days.ago", "--all"],
        repo_path,
        timeout,
        on_output=on_output,
    )
    if rc == 0:
        return True, f"Reflog entries >{days}d expired"
    return False, stderr.strip() if stderr else "Reflog expire failed"
