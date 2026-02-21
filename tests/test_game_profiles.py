"""
Test suite for game profile validation.

Ensures all game profiles are valid JSON with required fields.
"""

import asyncio
import json
from pathlib import Path

import pytest


def get_all_game_profiles():
    """Get all game profile JSON files."""
    profiles_dir = Path("game_profiles")
    profile_files = []

    # Get all JSON files in game_profiles directory
    for json_file in profiles_dir.rglob("*.json"):
        profile_files.append(json_file)

    return profile_files


async def load_game_profile_async(profile_path):
    """Load and parse a game profile JSON file asynchronously."""
    import aiofiles

    async with aiofiles.open(profile_path, encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)


def load_game_profile(profile_path):
    """Load and parse a game profile JSON file (sync wrapper for backwards compatibility)."""
    return asyncio.run(load_game_profile_async(profile_path))


class TestGameProfiles:
    """Test game profile validation."""

    @pytest.mark.parametrize("profile_path", get_all_game_profiles())
    def test_profile_is_valid_json(self, profile_path):
        """Test that profile is valid JSON."""
        try:
            load_game_profile(profile_path)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in {profile_path}: {e}")

    @pytest.mark.parametrize("profile_path", get_all_game_profiles())
    def test_profile_has_required_fields(self, profile_path):
        """Test that each game has all required fields."""
        required_fields = {
            "name",
            "executable",
            "ports",
            "protocol",
            "broadcast",
            "multicast",
            "keepalive",
            "mtu",
            "description",
            "low_latency",
            "high_bandwidth",
            "packet_priority",
        }

        profile = load_game_profile(profile_path)

        for game_id, game_data in profile.items():
            # Skip comment fields
            if game_id.startswith("_"):
                continue

            # Skip if game_data is not a dict (e.g., string comments)
            if not isinstance(game_data, dict):
                continue

            missing_fields = required_fields - set(game_data.keys())
            if missing_fields:
                pytest.fail(
                    f"Game '{game_id}' in {profile_path} missing fields: {missing_fields}"
                )

    @pytest.mark.parametrize("profile_path", get_all_game_profiles())
    def test_profile_field_types(self, profile_path):
        """Test that fields have correct types."""
        profile = load_game_profile(profile_path)

        for game_id, game_data in profile.items():
            # Skip comment fields
            if game_id.startswith("_") or not isinstance(game_data, dict):
                continue

            # String fields
            assert isinstance(game_data["name"], str), f"{game_id}: name must be string"
            assert isinstance(
                game_data["executable"], str
            ), f"{game_id}: executable must be string"
            assert isinstance(
                game_data["protocol"], str
            ), f"{game_id}: protocol must be string"
            assert isinstance(
                game_data["description"], str
            ), f"{game_id}: description must be string"
            assert isinstance(
                game_data["packet_priority"], str
            ), f"{game_id}: packet_priority must be string"

            # List fields
            assert isinstance(
                game_data["ports"], list
            ), f"{game_id}: ports must be list"
            assert all(
                isinstance(p, int) for p in game_data["ports"]
            ), f"{game_id}: ports must be integers"

            # Boolean fields
            assert isinstance(
                game_data["broadcast"], bool
            ), f"{game_id}: broadcast must be boolean"
            assert isinstance(
                game_data["multicast"], bool
            ), f"{game_id}: multicast must be boolean"
            assert isinstance(
                game_data["low_latency"], bool
            ), f"{game_id}: low_latency must be boolean"
            assert isinstance(
                game_data["high_bandwidth"], bool
            ), f"{game_id}: high_bandwidth must be boolean"

            # Integer fields
            assert isinstance(
                game_data["keepalive"], int
            ), f"{game_id}: keepalive must be integer"
            assert isinstance(game_data["mtu"], int), f"{game_id}: mtu must be integer"

            # Optional mod support fields
            if "mod_support" in game_data:
                mod_support = game_data["mod_support"]
                assert isinstance(
                    mod_support, dict
                ), f"{game_id}: mod_support must be object"
                if "mode" in mod_support:
                    assert isinstance(
                        mod_support["mode"], str
                    ), f"{game_id}: mod_support.mode must be string"
                if (
                    "native_provider" in mod_support
                    and mod_support["native_provider"] is not None
                ):
                    assert isinstance(
                        mod_support["native_provider"], str
                    ), f"{game_id}: mod_support.native_provider must be string or null"
                if "verify_method" in mod_support:
                    assert isinstance(
                        mod_support["verify_method"], str
                    ), f"{game_id}: mod_support.verify_method must be string"
                if "required_artifacts" in mod_support:
                    assert isinstance(
                        mod_support["required_artifacts"], list
                    ), f"{game_id}: mod_support.required_artifacts must be list"
                    assert all(
                        isinstance(item, str)
                        for item in mod_support["required_artifacts"]
                    ), f"{game_id}: mod_support.required_artifacts entries must be strings"
                if "notes" in mod_support:
                    assert isinstance(
                        mod_support["notes"], str
                    ), f"{game_id}: mod_support.notes must be string"

    @pytest.mark.parametrize("profile_path", get_all_game_profiles())
    def test_profile_field_values(self, profile_path):
        """Test that fields have valid values."""
        profile = load_game_profile(profile_path)

        for game_id, game_data in profile.items():
            # Skip comment fields
            if game_id.startswith("_") or not isinstance(game_data, dict):
                continue

            # Protocol must be valid
            assert game_data["protocol"] in [
                "udp",
                "tcp",
                "both",
            ], f"{game_id}: protocol must be 'udp', 'tcp', or 'both'"

            # Packet priority must be valid
            assert game_data["packet_priority"] in [
                "low",
                "medium",
                "high",
            ], f"{game_id}: packet_priority must be 'low', 'medium', or 'high'"

            # Ports must be in valid range
            for port in game_data["ports"]:
                assert (
                    1 <= port <= 65535
                ), f"{game_id}: port {port} out of range (1-65535)"

            # Keepalive must be reasonable
            assert (
                5 <= game_data["keepalive"] <= 60
            ), f"{game_id}: keepalive {game_data['keepalive']} out of range (5-60)"

            # MTU must be reasonable
            assert (
                1280 <= game_data["mtu"] <= 1500
            ), f"{game_id}: MTU {game_data['mtu']} out of range (1280-1500)"

            # Optional mod support validation
            if "mod_support" in game_data:
                mod_support = game_data["mod_support"]
                mode = mod_support.get("mode", "managed")
                assert mode in [
                    "native",
                    "managed",
                    "hybrid",
                ], f"{game_id}: mod_support.mode must be 'native', 'managed', or 'hybrid'"

                verify_method = mod_support.get("verify_method", "id_list")
                assert verify_method in [
                    "id_list",
                    "hash_list",
                    "none",
                ], (
                    f"{game_id}: mod_support.verify_method must be "
                    "'id_list', 'hash_list', or 'none'"
                )

    @pytest.mark.parametrize("profile_path", get_all_game_profiles())
    def test_no_duplicate_game_ids(self, profile_path):
        """Test that there are no duplicate game IDs within a profile."""
        profile = load_game_profile(profile_path)
        # Filter out comment fields
        game_ids = [gid for gid in profile if not gid.startswith("_")]

        assert len(game_ids) == len(
            set(game_ids)
        ), f"Duplicate game IDs found in {profile_path}"

    def test_no_duplicate_game_ids_across_profiles(self):
        """Test that there are no duplicate game IDs across all profiles."""
        all_game_ids = []

        for profile_path in get_all_game_profiles():
            profile = load_game_profile(profile_path)
            # Filter out comment fields
            game_ids = [gid for gid in profile if not gid.startswith("_")]
            all_game_ids.extend(game_ids)

        duplicates = [gid for gid in set(all_game_ids) if all_game_ids.count(gid) > 1]

        assert not duplicates, f"Duplicate game IDs across profiles: {duplicates}"

    def test_total_game_count(self):
        """Test that we have a reasonable number of games."""
        total_games = 0

        for profile_path in get_all_game_profiles():
            profile = load_game_profile(profile_path)
            # Filter out comment fields
            game_count = len([gid for gid in profile if not gid.startswith("_")])
            total_games += game_count

        # We should have at least 75 games
        assert (
            total_games >= 75
        ), f"Only {total_games} games found, expected at least 75"

        print(f"\n✅ Total games validated: {total_games}")
