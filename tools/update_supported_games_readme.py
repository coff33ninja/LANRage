"""Update README supported games section from game_profiles JSON."""

from __future__ import annotations

import json
from pathlib import Path

START_MARKER = "<!-- SUPPORTED_GAMES:START -->"
END_MARKER = "<!-- SUPPORTED_GAMES:END -->"


def load_profiles(base_dir: Path) -> dict[str, dict]:
    """Load all profile entries across JSON files."""
    profiles: dict[str, dict] = {}
    for path in sorted(base_dir.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for game_id, payload in data.items():
            if game_id.startswith("_") or not isinstance(payload, dict):
                continue
            entry = dict(payload)
            entry["_source_file"] = path.relative_to(base_dir).as_posix()
            profiles[game_id] = entry
    return profiles


def source_counts(profiles: dict[str, dict]) -> list[tuple[str, int]]:
    """Count profiles by source JSON file."""
    counts: dict[str, int] = {}
    for payload in profiles.values():
        source = payload.get("_source_file", "unknown")
        counts[source] = counts.get(source, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def build_block(profiles: dict[str, dict]) -> str:
    """Generate markdown block for README markers."""
    total = len(profiles)
    sources = source_counts(profiles)
    sample_games = sorted(
        payload.get("name", game_id) for game_id, payload in profiles.items()
    )[:24]

    lines = []
    lines.append("### Supported Games")
    lines.append("")
    lines.append(f"- Total profiles detected from `game_profiles/`: **{total}**")
    lines.append(
        "- Many entries in `game_profiles/custom/` are **community-seeded and untested**."
    )
    lines.append(
        "- Custom/community entries may be based on publicly available documentation and **Google search results**; validate ports/process names in your environment."
    )
    lines.append("")
    lines.append("Current profile sources:")
    for source, count in sources:
        lines.append(f"- `{source}`: {count}")
    lines.append("")
    lines.append("Sample supported games:")
    for game in sample_games:
        lines.append(f"- {game}")
    lines.append("")
    lines.append(
        "If a game fails detection, create or adjust a custom profile in `game_profiles/custom/`."
    )
    lines.append(
        "Full generated list: [`docs/SUPPORTED_GAMES.md`](docs/SUPPORTED_GAMES.md)."
    )
    return "\n".join(lines)


def build_supported_games_doc(profiles: dict[str, dict]) -> str:
    """Generate full supported games markdown document."""
    lines = []
    lines.append("# Supported Games")
    lines.append("")
    lines.append(
        "This file is auto-generated from `game_profiles/**/*.json` by `tools/update_supported_games_readme.py`."
    )
    lines.append("")
    lines.append(f"Total game profiles: **{len(profiles)}**")
    lines.append("")
    lines.append("## Disclaimer")
    lines.append("")
    lines.append(
        "- Many entries in `game_profiles/custom/` are community-seeded and untested."
    )
    lines.append(
        "- Custom/community entries may be based on public docs and Google search results."
    )
    lines.append(
        "- Port/process details may vary by platform, patch level, launcher, and mods."
    )
    lines.append("")
    lines.append("## All Profiles")
    lines.append("")
    lines.append("| Game ID | Name | Source |")
    lines.append("|---|---|---|")
    for game_id, payload in sorted(profiles.items(), key=lambda item: item[0]):
        name = str(payload.get("name", game_id)).replace("|", "\\|")
        source = str(payload.get("_source_file", "unknown")).replace("|", "\\|")
        lines.append(f"| `{game_id}` | {name} | `{source}` |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    readme_path = repo_root / "README.md"
    profiles_root = repo_root / "game_profiles"
    supported_games_doc_path = repo_root / "docs" / "SUPPORTED_GAMES.md"

    readme_text = readme_path.read_text(encoding="utf-8")
    if START_MARKER not in readme_text or END_MARKER not in readme_text:
        raise SystemExit(
            "README markers not found. Add SUPPORTED_GAMES start/end markers."
        )

    profiles = load_profiles(profiles_root)
    block = build_block(profiles)
    replacement = f"{START_MARKER}\n{block}\n{END_MARKER}"

    start = readme_text.index(START_MARKER)
    end = readme_text.index(END_MARKER) + len(END_MARKER)
    updated = readme_text[:start] + replacement + readme_text[end:]

    if updated != readme_text:
        readme_path.write_text(updated, encoding="utf-8")
        print("README supported games block updated.")
    else:
        print("README supported games block already up to date.")

    games_doc = build_supported_games_doc(profiles)
    old_games_doc = ""
    if supported_games_doc_path.exists():
        old_games_doc = supported_games_doc_path.read_text(encoding="utf-8")
    if games_doc != old_games_doc:
        supported_games_doc_path.write_text(games_doc, encoding="utf-8")
        print("docs/SUPPORTED_GAMES.md updated.")
    else:
        print("docs/SUPPORTED_GAMES.md already up to date.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
