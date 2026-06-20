import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class BranchInfo:
    name: str
    commit_date: datetime
    is_current: bool
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
            "--format=%(refname:short)%00%(committerdate:unix)%00%(HEAD)",
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
        if len(parts) < 3:
            continue
        name = parts[0]
        ts = int(parts[1])
        is_current = parts[2] == "*"
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)

        if since is not None and dt < since:
            continue
        if until is not None and dt > until:
            continue

        branches.append(
            BranchInfo(name=name, commit_date=dt, is_current=is_current)
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


def run_gc(
    repo_path: Path,
    aggressive: bool = False,
    timeout: int = 300,
) -> tuple[bool, str]:
    """Run ``git gc`` (optionally ``--aggressive``).

    Returns ``(success, message)``.
    """
    cmd = ["git", "gc"]
    if aggressive:
        cmd.append("--aggressive")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=repo_path, timeout=timeout
        )
        if result.returncode == 0:
            label = "GC (aggressive)" if aggressive else "GC"
            return True, f"{label} completed"
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, f"GC timed out after {timeout}s"


def repack_objects(
    repo_path: Path,
    timeout: int = 300,
) -> tuple[bool, str]:
    """Run ``git repack -Ad`` to optimize pack files."""
    try:
        result = subprocess.run(
            ["git", "repack", "-Ad"],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, "Repack completed"
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, f"Repack timed out after {timeout}s"


def prune_remote(
    repo_path: Path,
    remote: str = "origin",
    timeout: int = 30,
) -> tuple[bool, str]:
    """Run ``git remote prune <remote>`` to clean stale remote-tracking refs."""
    try:
        result = subprocess.run(
            ["git", "remote", "prune", remote],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, f"Remote '{remote}' pruned"
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, f"Prune timed out after {timeout}s"


def expire_reflog(
    repo_path: Path,
    days: int = 90,
    timeout: int = 60,
) -> tuple[bool, str]:
    """Expire reflog entries older than *days* days."""
    try:
        result = subprocess.run(
            ["git", "reflog", "expire", f"--expire={days}.days.ago", "--all"],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, f"Reflog entries >{days}d expired"
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, f"Reflog expire timed out after {timeout}s"
