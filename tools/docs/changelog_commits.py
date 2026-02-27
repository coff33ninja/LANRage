"""Generate markdown-ready commit traces for changelog updates.

Examples:
  python tools/docs/changelog_commits.py
  python tools/docs/changelog_commits.py --since 1.4.0
  python tools/docs/changelog_commits.py --since v1.4.0 --limit 20
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--since",
        help="Base git ref to compare from. Defaults to latest tag.",
    )
    parser.add_argument(
        "--until",
        default="HEAD",
        help="Target git ref to compare to (default: HEAD).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of commits to print (default: 50).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    since_ref = args.since
    if not since_ref:
        since_ref = git("describe", "--tags", "--abbrev=0", cwd=repo_root)

    rev_range = f"{since_ref}..{args.until}"
    log_output = git(
        "log",
        "--reverse",
        f"--max-count={args.limit}",
        "--pretty=format:%h|%cs|%s",
        rev_range,
        cwd=repo_root,
    )

    print(f"### Commit Trace ({rev_range})")
    if not log_output:
        print("- No commits in range.")
        return 0

    for line in log_output.splitlines():
        commit_id, commit_date, subject = line.split("|", maxsplit=2)
        print(f"- `{commit_id}` ({commit_date}) {subject}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
