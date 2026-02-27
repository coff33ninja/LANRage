"""Prevent reintroduction of legacy shim imports in Python modules."""

from __future__ import annotations

import re
from pathlib import Path

LEGACY_MODULES = (
    "network",
    "nat",
    "ipam",
    "connection",
    "control",
    "control_client",
    "party",
    "settings",
    "discord_integration",
    "updater",
    "logging_config",
    "metrics",
    "profiler",
    "games",
    "mod_sync",
    "server_browser",
    "broadcast",
)

LEGACY_IMPORT_RE = re.compile(
    rf"^\s*(?:from|import)\s+core\.(?:{'|'.join(LEGACY_MODULES)})\b",
    re.MULTILINE,
)


def test_no_legacy_core_imports_in_python_modules() -> None:
    """Fail if python files import migrated modules via old paths."""
    repo_root = Path(__file__).resolve().parent.parent
    offenders: list[str] = []

    for path in repo_root.rglob("*.py"):
        rel = path.relative_to(repo_root)
        if ".venv" in path.parts:
            continue

        text = path.read_text(encoding="utf-8")
        if LEGACY_IMPORT_RE.search(text):
            offenders.append(str(rel).replace("\\", "/"))

    assert not offenders, "Legacy core imports found:\n" + "\n".join(sorted(offenders))
