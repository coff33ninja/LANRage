"""Mod manifest planning and download helpers for LANrage."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import aiofiles


def _normalize_id(value: str) -> str:
    """Normalize artifact IDs for stable matching."""
    return value.strip().lower()


def compute_sha256(path: Path) -> str:
    """Compute SHA256 for a file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


@dataclass(slots=True)
class ModArtifact:
    """Single artifact in a mod manifest."""

    artifact_id: str
    relative_path: str
    sha256: str = ""
    size_bytes: int = 0
    source_urls: list[str] = field(default_factory=list)

    def normalized_id(self) -> str:
        """Normalized artifact ID."""
        return _normalize_id(self.artifact_id)


@dataclass(slots=True)
class ModManifest:
    """Mod manifest shared by host/peers."""

    game_id: str
    version: str
    artifacts: list[ModArtifact]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModManifest:
        """Build manifest from raw dictionary data."""
        artifacts = [
            ModArtifact(
                artifact_id=item["artifact_id"],
                relative_path=item.get("relative_path", item["artifact_id"]),
                sha256=item.get("sha256", ""),
                size_bytes=item.get("size_bytes", 0),
                source_urls=item.get("source_urls", []),
            )
            for item in data.get("artifacts", [])
        ]
        return cls(
            game_id=data["game_id"],
            version=data.get("version", "0"),
            artifacts=artifacts,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize manifest to dictionary."""
        return {
            "game_id": self.game_id,
            "version": self.version,
            "artifacts": [asdict(artifact) for artifact in self.artifacts],
        }

    def fingerprint(self) -> str:
        """Stable manifest fingerprint."""
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ModSyncService:
    """Plans and executes mod sync workflows."""

    async def inspect_local_state(
        self, manifest: ModManifest, mods_root: Path
    ) -> dict[str, list[str]]:
        """
        Inspect local mod state against manifest.

        Returns IDs grouped into present/missing/corrupt.
        """
        present: list[str] = []
        missing: list[str] = []
        corrupt: list[str] = []

        for artifact in manifest.artifacts:
            artifact_path = mods_root / artifact.relative_path
            normalized = artifact.normalized_id()

            if not artifact_path.exists():
                missing.append(normalized)
                continue

            if artifact.sha256:
                local_hash = compute_sha256(artifact_path)
                if local_hash.lower() != artifact.sha256.lower():
                    corrupt.append(normalized)
                    continue

            present.append(normalized)

        return {"present": present, "missing": missing, "corrupt": corrupt}

    async def build_sync_plan(
        self,
        mode: str,
        manifest: ModManifest,
        mods_root: Path,
        native_provider: str | None = None,
        peer_sources: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build sync plan for native/managed/hybrid strategy."""
        state = await self.inspect_local_state(manifest, mods_root)
        needed = sorted(set(state["missing"] + state["corrupt"]))
        peer_sources = peer_sources or []

        if mode == "native":
            return {
                "mode": mode,
                "manifest_fingerprint": manifest.fingerprint(),
                "needed_artifacts": needed,
                "native_provider": native_provider,
                "lanrage_download_enabled": False,
                "ready": not needed,
                "next_step": (
                    "Use game-native mod downloader." if needed else "No sync required."
                ),
            }

        download_items: list[dict[str, Any]] = []
        by_id = {artifact.normalized_id(): artifact for artifact in manifest.artifacts}
        for artifact_id in needed:
            artifact = by_id.get(artifact_id)
            if artifact is None:
                continue

            sources = list(artifact.source_urls)
            for base in peer_sources:
                base_url = base.rstrip("/")
                sources.append(f"{base_url}/{artifact.relative_path}")

            download_items.append(
                {
                    "artifact_id": artifact_id,
                    "relative_path": artifact.relative_path,
                    "sha256": artifact.sha256,
                    "sources": sources,
                }
            )

        if mode == "hybrid":
            next_step = (
                "Resolve native dependencies, then download remaining via LANrage."
                if needed
                else "No sync required."
            )
        else:
            next_step = "Download missing/corrupt artifacts via LANrage."

        return {
            "mode": mode,
            "manifest_fingerprint": manifest.fingerprint(),
            "needed_artifacts": needed,
            "native_provider": native_provider,
            "lanrage_download_enabled": True,
            "ready": not needed,
            "next_step": next_step if needed else "No sync required.",
            "downloads": download_items,
        }

    async def write_manifest(self, manifest: ModManifest, path: Path) -> None:
        """Write manifest to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w", encoding="utf-8") as handle:
            await handle.write(json.dumps(manifest.to_dict(), indent=2))
