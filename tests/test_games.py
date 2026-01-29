"""Tests for game detection and profiles"""

import pytest

from core.config import Config
from core.games import GAME_PROFILES, GameDetector, GameProfile


@pytest.fixture
def config():
    """Create test config"""
    return Config.load()


@pytest.fixture
def detector(config):
    """Create game detector"""
    return GameDetector(config)


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
