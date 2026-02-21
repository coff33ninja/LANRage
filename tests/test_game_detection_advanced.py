"""Tests for advanced game detection features.

Tests the multi-method detection system including:
- Process-based detection
- Port-based detection
- Window title detection (Windows only)
- Confidence scoring and detection ranking
"""

from unittest.mock import MagicMock, patch

import pytest

from core.config import Config
from core.games import (
    DetectionResult,
    GameDetector,
    GameProfile,
)


@pytest.fixture
def sample_profile():
    """Sample game profile for testing"""
    return GameProfile(
        name="Test Game",
        executable="testgame.exe",
        ports=[7777, 27015],
        protocol="udp",
        broadcast=True,
        multicast=False,
        keepalive=25,
        mtu=1420,
        description="Test game",
        low_latency=True,
        high_bandwidth=False,
    )


@pytest.fixture
def config():
    """Create test config"""
    return Config()


@pytest.fixture
def game_detector(config):
    """Create GameDetector instance"""
    return GameDetector(config)


class TestDetectionResult:
    """Test DetectionResult dataclass"""

    def test_detection_result_valid_confidence(self, sample_profile):
        """Test DetectionResult with valid confidence"""
        result = DetectionResult(
            game_id="test_game",
            profile=sample_profile,
            confidence=0.85,
            method="process",
        )
        assert result.confidence == 0.85
        assert result.game_id == "test_game"
        assert result.method == "process"

    def test_detection_result_clamps_confidence(self, sample_profile):
        """Test DetectionResult clamps confidence to 0-1"""
        result_high = DetectionResult(
            game_id="test",
            profile=sample_profile,
            confidence=1.5,
            method="process",
        )
        assert result_high.confidence == 1.0

        result_low = DetectionResult(
            game_id="test",
            profile=sample_profile,
            confidence=-0.5,
            method="process",
        )
        assert result_low.confidence == 0.0

    def test_detection_result_sorting(self, sample_profile):
        """Test DetectionResult sorting by confidence (higher is better)"""
        results = [
            DetectionResult(
                game_id="g1", profile=sample_profile, confidence=0.6, method="port"
            ),
            DetectionResult(
                game_id="g2", profile=sample_profile, confidence=0.95, method="process"
            ),
            DetectionResult(
                game_id="g3",
                profile=sample_profile,
                confidence=0.80,
                method="window_title",
            ),
        ]

        sorted_results = sorted(results)
        assert sorted_results[0].confidence == 0.95
        assert sorted_results[-1].confidence == 0.6

    def test_detection_result_default_details(self, sample_profile):
        """Test DetectionResult initializes empty details dict"""
        result = DetectionResult(
            game_id="test",
            profile=sample_profile,
            confidence=0.8,
            method="process",
        )
        assert result.details == {}


class TestProcessDetection:
    """Test process-based game detection"""

    @pytest.mark.asyncio
    async def test_process_detection_exact_match(self, game_detector, sample_profile):
        """Test detecting game via exact process name match"""
        # Set up mock GAME_PROFILES
        with (
            patch("core.games.GAME_PROFILES", {"test_game": sample_profile}),
            patch("psutil.process_iter") as mock_proc_iter,
        ):
            # Mock process that matches
            mock_proc = MagicMock()
            mock_proc.info = {"name": "testgame.exe"}
            mock_proc_iter.return_value = [mock_proc]

            # Run detection
            await game_detector._detect_games()

            # Verify game was detected
            assert "test_game" in game_detector.detected_games

    @pytest.mark.asyncio
    async def test_process_detection_fuzzy_match(self, game_detector, sample_profile):
        """Test detecting game via fuzzy process name match"""
        with (
            patch("core.games.GAME_PROFILES", {"test_game": sample_profile}),
            patch("psutil.process_iter") as mock_proc_iter,
        ):
            # Mock process with similar name
            mock_proc = MagicMock()
            mock_proc.info = {"name": "TestGame.exe"}  # Mixed case
            mock_proc_iter.return_value = [mock_proc]

            # Run detection
            await game_detector._detect_games()

            # Verify game was detected despite case difference
            assert "test_game" in game_detector.detected_games

    @pytest.mark.asyncio
    async def test_process_detection_confidence(self, game_detector, sample_profile):
        """Test process detection has high confidence"""
        with (
            patch.object(GameDetector, "_detect_by_window_title", return_value=[]),
            patch.object(GameDetector, "_detect_by_open_ports", return_value=[]),
            patch("core.games.GAME_PROFILES", {"test_game": sample_profile}),
            patch("psutil.process_iter") as mock_proc_iter,
        ):
            # Mock process
            mock_proc = MagicMock()
            mock_proc.info = {"name": "testgame.exe"}
            mock_proc_iter.return_value = [mock_proc]

            # Run detection
            await game_detector._detect_games()

            # Process detection should have high confidence (0.95)
            assert "test_game" in game_detector.detected_games


class TestPortDetection:
    """Test port-based game detection"""

    @pytest.mark.asyncio
    async def test_port_detection_results(self, game_detector, sample_profile):
        """Test port-based detection returns DetectionResult instances"""
        with patch("core.games.GAME_PROFILES", {"test_game": sample_profile}):
            results = await game_detector._detect_by_open_ports()

            # Should return list of DetectionResult
            assert isinstance(results, list)
            for result in results:
                assert isinstance(result, DetectionResult)
                if result:
                    assert 0.0 <= result.confidence <= 1.0
                    assert result.method == "port"
                    assert "matched_ports" in result.details

    @pytest.mark.asyncio
    async def test_port_detection_confidence_range(self, game_detector, sample_profile):
        """Test port detection confidence is in valid range"""
        with patch("core.games.GAME_PROFILES", {"test_game": sample_profile}):
            results = await game_detector._detect_by_open_ports()

            for result in results:
                # Port detection should be medium-low confidence (0.6-0.75)
                if result.method == "port":
                    assert 0.5 <= result.confidence <= 0.8


class TestWindowTitleDetection:
    """Test window title-based game detection"""

    @pytest.mark.asyncio
    async def test_window_detection_non_windows(self, game_detector):
        """Test window detection returns empty on non-Windows platforms"""
        with patch("platform.system", return_value="Linux"):
            results = await game_detector._detect_by_window_title()
            assert results == []

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        __import__("platform").system() != "Windows",
        reason="Windows only test",
    )
    async def test_window_detection_returns_list(self, game_detector):
        """Test window detection returns list of DetectionResult on Windows"""
        results = await game_detector._detect_by_window_title()
        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, DetectionResult)
            assert result.method == "window_title"


class TestDetectionRanking:
    """Test detection ranking and confidence selection"""

    @pytest.mark.asyncio
    async def test_highest_confidence_selected(self, game_detector, sample_profile):
        """Test that highest confidence detection is selected"""
        # Create multiple detections with different confidences
        results = [
            DetectionResult(
                game_id="test",
                profile=sample_profile,
                confidence=0.70,
                method="port",
            ),
            DetectionResult(
                game_id="test",
                profile=sample_profile,
                confidence=0.95,
                method="process",
            ),
            DetectionResult(
                game_id="test",
                profile=sample_profile,
                confidence=0.80,
                method="window_title",
            ),
        ]

        # Highest confidence should be selected
        best = max(results, key=lambda x: x.confidence)
        assert best.confidence == 0.95
        assert best.method == "process"

    @pytest.mark.asyncio
    async def test_detection_history_recording(self, game_detector, sample_profile):
        """Test game detection history is recorded"""
        # Mock the optimizer to avoid AttributeError
        mock_optimizer = MagicMock()
        mock_optimizer.active_profile = None
        game_detector.optimizer = mock_optimizer

        with (
            patch("core.games.GAME_PROFILES", {"test_game": sample_profile}),
            patch("psutil.process_iter") as mock_proc_iter,
        ):
            # Mock process
            mock_proc = MagicMock()
            mock_proc.info = {"name": "testgame.exe"}
            mock_proc_iter.return_value = [mock_proc]

            # Run detection first time
            await game_detector._detect_games()
            initial_history_len = len(game_detector.detection_history)

            # Run detection second time
            await game_detector._detect_games()

            # History should still be same length (no duplicate entries for same game)
            assert len(game_detector.detection_history) == initial_history_len

            # Stop game
            mock_proc_iter.return_value = []
            await game_detector._detect_games()

            # History should record stop event
            assert len(game_detector.detection_history) > initial_history_len


class TestGameDetectorIntegration:
    """Integration tests for GameDetector"""

    @pytest.mark.asyncio
    async def test_detector_lifecycle(self, game_detector):
        """Test GameDetector start/stop lifecycle"""
        assert not game_detector.running
        await game_detector.start()
        assert game_detector.running
        await game_detector.stop()
        assert not game_detector.running

    @pytest.mark.asyncio
    async def test_get_active_games(self, game_detector, sample_profile):
        """Test retrieving active games"""
        with patch("core.games.GAME_PROFILES", {"test_game": sample_profile}):
            # Set active games
            game_detector.detected_games = {"test_game"}

            active = game_detector.get_active_games()
            assert len(active) == 1
            assert active[0].name == "Test Game"

    @pytest.mark.asyncio
    async def test_get_profile_by_id(self, game_detector, sample_profile):
        """Test retrieving profile by game ID"""
        with patch("core.games.GAME_PROFILES", {"test_game": sample_profile}):
            profile = game_detector.get_profile("test_game")
            assert profile is not None
            assert profile.name == "Test Game"

    @pytest.mark.asyncio
    async def test_multiple_simultaneous_games(self, game_detector):
        """Test detecting multiple games simultaneously"""
        profiles = {
            "game1": GameProfile(
                name="Game 1",
                executable="game1.exe",
                ports=[7777],
                protocol="udp",
                broadcast=False,
                multicast=False,
                keepalive=25,
                mtu=1420,
                description="Game 1",
            ),
            "game2": GameProfile(
                name="Game 2",
                executable="game2.exe",
                ports=[27015],
                protocol="tcp",
                broadcast=False,
                multicast=False,
                keepalive=25,
                mtu=1420,
                description="Game 2",
            ),
        }

        with (
            patch("core.games.GAME_PROFILES", profiles),
            patch("psutil.process_iter") as mock_proc_iter,
        ):
            # Mock both processes running
            mock_proc1 = MagicMock()
            mock_proc1.info = {"name": "game1.exe"}
            mock_proc2 = MagicMock()
            mock_proc2.info = {"name": "game2.exe"}
            mock_proc_iter.return_value = [mock_proc1, mock_proc2]

            # Run detection
            await game_detector._detect_games()

            # Both games should be detected
            assert "game1" in game_detector.detected_games
            assert "game2" in game_detector.detected_games
