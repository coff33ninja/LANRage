"""Synchronize README version references with a target version."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def infer_version_from_pyproject(pyproject_path: Path) -> str:
    """Read project version from pyproject.toml without extra deps."""
    text = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)


def update_readme(readme_path: Path, version: str) -> bool:
    """Update README badge/status version fields."""
    text = readme_path.read_text(encoding="utf-8")
    updated = text

    updated = re.sub(
        r"(\[!\[Version\]\(https://img\.shields\.io/badge/version-)[0-9]+\.[0-9]+\.[0-9]+(-brightgreen\.svg\)\(CHANGELOG\.md\)\))",
        rf"\g<1>{version}\g<2>",
        updated,
    )
    updated = re.sub(
        r"(✅\s+\*\*v)[0-9]+\.[0-9]+\.[0-9]+(\s+-\s+PRODUCTION READY\*\*)",
        rf"\g<1>{version}\g<2>",
        updated,
    )

    changed = updated != text
    if changed:
        readme_path.write_text(updated, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="Version string like 1.3.0")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    pyproject_path = repo_root / "pyproject.toml"
    readme_path = repo_root / "README.md"

    version = args.version or infer_version_from_pyproject(pyproject_path)
    changed = update_readme(readme_path, version)
    print(f"README version synchronized to {version}. changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
