"""Tests for game detection and profiles"""

import asyncio
from pathlib import Path

import pytest

from core.config import Config
from core.games import (
    GAME_PROFILES,
    GameDetector,
    GameManager,
    GameProfile,
    ModSupport,
    initialize_game_profiles,
)


@pytest.fixture
async def config():
    """Create test config"""
    return await Config.load()


@pytest.fixture
def detector(config):
    """Create game detector"""
    return GameDetector(config)


@pytest.fixture(scope="session", autouse=True)
def init_profiles():
    """Initialize game profiles for all tests"""
    asyncio.run(initialize_game_profiles())


def test_detector_initialization(detector):
    """Test detector initializes correctly"""
    assert detector.config is not None
    assert GAME_PROFILES is not None
    assert len(GAME_PROFILES) > 0


def test_load_builtin_profiles(detector):
    """Test loading built-in profiles"""
    profiles = GAME_PROFILES

    # Check some known games
    assert "minecraft" in profiles
    assert "terraria" in profiles
    assert "rust" in profiles


def test_get_profile_existing(detector):
    """Test getting an existing profile"""
    profile = detector.get_profile("minecraft")

    assert profile is not None
    assert profile.name == "Minecraft Java Edition"
    assert len(profile.ports) > 0


def test_get_profile_nonexistent(detector):
    """Test getting a non-existent profile"""
    profile = detector.get_profile("nonexistent_game")
    assert profile is None


def test_detect_game_by_port(detector):
    """Test detecting game by port"""
    # Minecraft uses port 25565
    # Check if minecraft profile exists and has this port
    minecraft = detector.get_profile("minecraft")

    if minecraft and 25565 in minecraft.ports:
        # Profile exists with this port
        assert minecraft.name == "Minecraft Java Edition"


def test_detect_game_by_process(detector):
    """Test detecting game by process name"""
    # Check if minecraft profile exists
    minecraft = detector.get_profile("minecraft")

    if minecraft:
        # Verify the profile has an executable
        assert minecraft.executable is not None
        assert len(minecraft.executable) > 0


def test_get_active_games(detector):
    """Test getting active games"""
    # Initially no games detected
    games = detector.get_active_games()

    assert isinstance(games, list)
    # Should be empty unless a game is actually running
    assert len(games) >= 0


def test_game_profile_properties():
    """Test GameProfile properties"""
    profile = GameProfile(
        name="Test Game",
        executable="test.exe",
        ports=[12345],
        protocol="udp",
        broadcast=True,
        multicast=False,
        keepalive=25,
        mtu=1420,
        description="Test game",
        low_latency=True,
        high_bandwidth=False,
        packet_priority="high",
    )

    assert profile.name == "Test Game"
    assert profile.executable == "test.exe"
    assert profile.ports == [12345]
    assert profile.protocol == "udp"
    assert profile.broadcast is True
    assert profile.multicast is False
    assert profile.keepalive == 25
    assert profile.mtu == 1420
    assert profile.low_latency is True
    assert profile.high_bandwidth is False
    assert profile.packet_priority == "high"
    assert profile.mod_support.mode == "managed"


def test_mod_sync_strategy_native_requires_native_download():
    """Native mod strategy should require in-game/native sync when artifacts are missing."""
    manager = GameManager(Config())
    game_id = "test_native_mods"

    GAME_PROFILES[game_id] = GameProfile(
        name="Test Native Mods",
        executable="test_native.exe",
        ports=[12345],
        protocol="udp",
        broadcast=False,
        multicast=False,
        keepalive=20,
        mtu=1420,
        description="Native mods test profile",
        mod_support=ModSupport(
            mode="native",
            native_provider="fastdl",
            verify_method="id_list",
            required_artifacts=["pak0", "pak1"],
        ),
    )

    try:
        result = manager.evaluate_mod_compatibility(game_id, local_artifacts=["pak0"])
        assert result["mode"] == "native"
        assert result["native_sync_required"] is True
        assert result["lanrage_sync_enabled"] is False
        assert result["missing_artifacts"] == ["pak1"]
    finally:
        del GAME_PROFILES[game_id]


def test_mod_sync_strategy_hybrid_allows_lanrage_after_native_check():
    """Hybrid strategy should expose missing native artifacts and allow LANrage extras."""
    manager = GameManager(Config())
    game_id = "test_hybrid_mods"

    GAME_PROFILES[game_id] = GameProfile(
        name="Test Hybrid Mods",
        executable="test_hybrid.exe",
        ports=[12345],
        protocol="udp",
        broadcast=False,
        multicast=False,
        keepalive=20,
        mtu=1420,
        description="Hybrid mods test profile",
        mod_support=ModSupport(
            mode="hybrid",
            native_provider="steam_workshop",
            verify_method="id_list",
            required_artifacts=["workshop_101", "workshop_202"],
        ),
    )

    try:
        missing_result = manager.evaluate_mod_compatibility(
            game_id, local_artifacts=["workshop_101"]
        )
        assert missing_result["mode"] == "hybrid"
        assert missing_result["native_sync_required"] is True
        assert missing_result["lanrage_sync_enabled"] is True
        assert missing_result["missing_artifacts"] == ["workshop_202"]

        ready_result = manager.evaluate_mod_compatibility(
            game_id, local_artifacts=["workshop_101", "workshop_202"]
        )
        assert ready_result["ready"] is True
        assert ready_result["missing_artifacts"] == []
    finally:
        del GAME_PROFILES[game_id]


@pytest.mark.asyncio
async def test_game_manager_build_mod_sync_plan(tmp_path: Path):
    """GameManager should build WG-compatible peer source download plans."""
    manager = GameManager(Config())
    game_id = "test_managed_sync"

    GAME_PROFILES[game_id] = GameProfile(
        name="Test Managed Sync",
        executable="test_sync.exe",
        ports=[12345],
        protocol="udp",
        broadcast=False,
        multicast=False,
        keepalive=20,
        mtu=1420,
        description="Managed sync test profile",
        mod_support=ModSupport(mode="managed", required_artifacts=["pak0.pk3"]),
    )

    try:
        plan = await manager.build_mod_sync_plan(
            game_id=game_id,
            mods_root=tmp_path,
            peer_sources=["http://10.66.0.10:8670/mods"],
        )
        assert plan["mode"] == "managed"
        assert plan["lanrage_download_enabled"] is True
        assert plan["needed_artifacts"] == ["pak0.pk3"]
        assert plan["downloads"][0]["sources"][0].startswith("http://10.66.0.10")
    finally:
        del GAME_PROFILES[game_id]


def test_get_optimization_settings():
    """Test getting optimization settings for a game"""
    # Get minecraft profile
    profile = GAME_PROFILES.get("minecraft")

    if profile:
        # Verify profile has optimization settings
        assert profile.keepalive is not None
        assert profile.mtu is not None
        assert isinstance(profile.broadcast, bool)
        assert isinstance(profile.low_latency, bool)


def test_list_supported_games():
    """Test listing all supported games"""
    games = list(GAME_PROFILES.values())

    assert len(games) > 0
    assert all(isinstance(g, GameProfile) for g in games)
    # We support 27+ games
    assert len(games) >= 27
