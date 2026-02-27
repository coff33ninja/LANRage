"""Synchronize project version references across README and docs."""

from __future__ import annotations

import argparse
import re
from datetime import UTC, datetime
from pathlib import Path


def infer_version_from_pyproject(pyproject_path: Path) -> str:
    """Read project version from pyproject.toml without extra deps."""
    text = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)


def apply_replacements(path: Path, replacements: list[tuple[str, str]]) -> bool:
    """Apply regex replacements to a file and return whether it changed."""
    text = path.read_text(encoding="utf-8")
    updated = text

    for pattern, repl in replacements:
        updated = re.sub(pattern, repl, updated, flags=re.MULTILINE)

    changed = updated != text
    if changed:
        path.write_text(updated, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="Version string like 1.3.1")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    pyproject_path = repo_root / "pyproject.toml"

    version = args.version or infer_version_from_pyproject(pyproject_path)
    today = datetime.now(UTC)
    pretty_date = f"{today.strftime('%B')} {today.day}, {today.year}"

    updates: dict[Path, list[tuple[str, str]]] = {
        repo_root
        / "README.md": [
            (
                r"(\[!\[Version\]\(https://img\.shields\.io/badge/version-)[0-9]+\.[0-9]+\.[0-9]+(-brightgreen\.svg\)\(CHANGELOG\.md\)\))",
                rf"\g<1>{version}\g<2>",
            ),
            (
                r"(✅\s+\*\*v)[0-9]+\.[0-9]+\.[0-9]+(\s+-\s+PRODUCTION READY\*\*)",
                rf"\g<1>{version}\g<2>",
            ),
        ],
        repo_root
        / "docs"
        / "README.md": [
            (r"(\*\*Version\*\*:\s*)[0-9]+\.[0-9]+\.[0-9]+", rf"\g<1>{version}"),
            (
                r"(\*\*Current Version\*\*:\s*)[0-9]+\.[0-9]+\.[0-9]+",
                rf"\g<1>{version}",
            ),
            (
                r"(\*\*Last Updated\*\*:\s*)[A-Za-z]+ \d{1,2}, \d{4}",
                rf"\g<1>{pretty_date}",
            ),
        ],
        repo_root
        / "docs"
        / "USER_GUIDE.md": [
            (r"(\*\*Version\*\*:\s*)[0-9]+\.[0-9]+\.[0-9]+", rf"\g<1>{version}"),
            (r"(🎮\s+LANrage v)[0-9]+\.[0-9]+\.[0-9]+", rf"\g<1>{version}"),
            (
                r"(\*\*Last Updated\*\*:\s*)[A-Za-z]+ \d{1,2}, \d{4}",
                rf"\g<1>{pretty_date}",
            ),
        ],
        repo_root
        / "docs"
        / "QUICKSTART.md": [
            (
                r"(Get LANrage v)[0-9]+\.[0-9]+\.[0-9]+(\s+running)",
                rf"\g<1>{version}\g<2>",
            ),
            (
                r"(LANrage v)[0-9]+\.[0-9]+\.[0-9]+(\s+is production-ready with:)",
                rf"\g<1>{version}\g<2>",
            ),
            (
                r"(LANrage v)[0-9]+\.[0-9]+\.[0-9]+(\s+- Production Ready)",
                rf"\g<1>{version}\g<2>",
            ),
        ],
        repo_root
        / "docs"
        / "ARCHITECTURE.md": [
            (
                r"(\*\*Status\*\*:\s+Production ready \(v)[0-9]+\.[0-9]+\.[0-9]+(\))",
                rf"\g<1>{version}\g<2>",
            ),
            (
                r"(### ✅ Completed \(v)[0-9]+\.[0-9]+\.[0-9]+(\))",
                rf"\g<1>{version}\g<2>",
            ),
        ],
        repo_root
        / "docs"
        / "DISCORD_RICH_PRESENCE_SETUP.md": [
            (
                r"(LANrage v)[0-9]+\.[0-9]+\.[0-9]+(\s+or higher)",
                rf"\g<1>{version}\g<2>",
            ),
            (
                r"(\*\*LANrage Version\*\*:\s+v)[0-9]+\.[0-9]+\.[0-9]+(\+)",
                rf"\g<1>{version}\g<2>",
            ),
            (
                r"(\*\*Last Updated\*\*:\s*)[A-Za-z]+ \d{1,2}, \d{4}",
                rf"\g<1>{pretty_date}",
            ),
        ],
        repo_root
        / "docs"
        / "CI_CD.md": [
            (
                r"(\*\*Last Updated\*\*:\s*)[A-Za-z]+ \d{1,2}, \d{4}",
                rf"\g<1>{pretty_date}",
            )
        ],
    }

    changed_files: list[str] = []
    for path, replacements in updates.items():
        if not path.exists():
            continue
        if apply_replacements(path, replacements):
            changed_files.append(str(path.relative_to(repo_root)))

    print(
        f"Version synchronization complete for {version}. "
        f"changed_files={len(changed_files)}"
    )
    for item in changed_files:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
