import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TUI tool for browsing and bulk-deleting git branches"
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Path to git repository (default: current directory)",
    )
    args = parser.parse_args()

    # Lazy import to allow --help to work even if TUI app has import issues
    from git_cleaner.app import GitCleanerApp  # noqa: PLC0415

    app = GitCleanerApp(repo_path=args.repo.resolve())
    app.run()
