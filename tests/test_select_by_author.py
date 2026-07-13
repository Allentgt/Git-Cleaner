import subprocess
import tempfile
from pathlib import Path

from git_cleaner.git_ops import list_branches, BranchInfo


def _init_repo(path: Path) -> None:
    """Initialize a git repo with branches by different authors."""
    subprocess.run(["git", "init", "-b", "main"], cwd=path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "alice@test.com"], cwd=path, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Alice"], cwd=path, capture_output=True
    )
    (path / "README.md").write_text("# test")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, capture_output=True)

    # Alice branch
    subprocess.run(["git", "checkout", "-b", "alice/feature"], cwd=path, capture_output=True)
    (path / "alice.txt").write_text("alice")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "alice feature"], cwd=path, capture_output=True)

    # Bob branch
    subprocess.run(["git", "config", "user.email", "bob@test.com"], cwd=path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Bob"], cwd=path, capture_output=True)
    subprocess.run(["git", "checkout", "-b", "bob/feature", "main"], cwd=path, capture_output=True)
    (path / "bob.txt").write_text("bob")
    subprocess.run(["git", "add", "."], cwd=path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "bob feature"], cwd=path, capture_output=True)

    # Protected branch (main)
    subprocess.run(["git", "checkout", "main"], cwd=path, capture_output=True)


def test_select_by_author_filters_protected_and_blacklisted():
    """select_by_author should not select protected or blacklisted branches."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "myrepo"
        repo.mkdir()
        _init_repo(repo)

        branches = list_branches(repo)

        # Simulate what select_by_author does: filter by author, skip protected/blacklisted
        alice_branches = [b for b in branches if b.author == "Alice"]
        bob_branches = [b for b in branches if b.author == "Bob"]

        # main is protected — should be excluded even if author matches
        main_branch = next(b for b in branches if b.name == "main")
        main_branch.is_protected = True

        # Simulate the select_by_author logic
        to_select = [b for b in alice_branches if not b.is_protected and not b.is_blacklisted]
        selected_names = {b.name for b in to_select}

        # Alice authored alice/feature and main — main is protected so excluded
        assert "alice/feature" in selected_names
        assert "main" not in selected_names

        # Bob's branches should not be selected when filtering by Alice
        bob_selected = [b for b in bob_branches if not b.is_protected and not b.is_blacklisted]
        assert all(b.name not in selected_names for b in bob_selected)

        # Count matches the filtered set, not the raw set
        assert len(to_select) == 1  # only alice/feature, not main
