"""Tests for mod sync planning and manifest handling."""

from pathlib import Path

import pytest

from core.mod_sync import ModManifest, ModSyncService


@pytest.mark.asyncio
async def test_manifest_fingerprint_is_stable():
    """Manifest fingerprint should be deterministic for equivalent data."""
    a = ModManifest.from_dict(
        {
            "game_id": "quake_live",
            "version": "1",
            "artifacts": [
                {"artifact_id": "pak0", "relative_path": "baseq3/pak0.pk3"},
                {"artifact_id": "pak1", "relative_path": "baseq3/pak1.pk3"},
            ],
        }
    )
    b = ModManifest.from_dict(
        {
            "game_id": "quake_live",
            "version": "1",
            "artifacts": [
                {"artifact_id": "pak0", "relative_path": "baseq3/pak0.pk3"},
                {"artifact_id": "pak1", "relative_path": "baseq3/pak1.pk3"},
            ],
        }
    )
    assert a.fingerprint() == b.fingerprint()


@pytest.mark.asyncio
async def test_native_mode_returns_native_action(tmp_path: Path):
    """Native mode should avoid LANrage download."""
    service = ModSyncService()
    manifest = ModManifest.from_dict(
        {
            "game_id": "cod4",
            "version": "1",
            "artifacts": [{"artifact_id": "map_a", "relative_path": "mods/map_a.ff"}],
        }
    )
    plan = await service.build_sync_plan(
        mode="native",
        manifest=manifest,
        mods_root=tmp_path,
        native_provider="fastdl",
    )
    assert plan["mode"] == "native"
    assert plan["lanrage_download_enabled"] is False
    assert plan["ready"] is False
    assert plan["needed_artifacts"] == ["map_a"]


@pytest.mark.asyncio
async def test_managed_mode_builds_download_urls(tmp_path: Path):
    """Managed mode should include peer download URLs for missing artifacts."""
    service = ModSyncService()
    manifest = ModManifest.from_dict(
        {
            "game_id": "quake_3_arena",
            "version": "2",
            "artifacts": [
                {"artifact_id": "pak0", "relative_path": "baseq3/pak0.pk3"},
            ],
        }
    )
    plan = await service.build_sync_plan(
        mode="managed",
        manifest=manifest,
        mods_root=tmp_path,
        peer_sources=["http://10.66.0.2:8670/mods"],
    )
    assert plan["lanrage_download_enabled"] is True
    assert len(plan["downloads"]) == 1
    assert (
        plan["downloads"][0]["sources"][0]
        == "http://10.66.0.2:8670/mods/baseq3/pak0.pk3"
    )
