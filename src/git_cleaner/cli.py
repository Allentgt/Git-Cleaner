import argparse
import sys
from pathlib import Path


def _print_splash() -> None:
    """Print the ANSI splash logo to stderr."""
    from git_cleaner.logo import PRESSSTART_LOGO  # noqa: PLC0415

    sys.stderr.buffer.write(PRESSSTART_LOGO + b"\n")
    sys.stderr.flush()


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
    parser.add_argument(
        "--no-splash",
        action="store_true",
        help="Suppress the ANSI splash logo",
    )
    args = parser.parse_args()

    if not args.no_splash:
        _print_splash()

    # Lazy import to avoid circular dependency and allow --help to work
    # even if the TUI app has import issues
    from git_cleaner.app import GitCleanerApp  # noqa: PLC0415

    app = GitCleanerApp(repo_path=args.repo.resolve())
    app.run()
