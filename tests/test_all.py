#!/usr/bin/env python3
"""
Comprehensive test suite for LANrage
Tests all components before moving to Phase 2
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.nat import NATError, NATTraversal
from core.network import NetworkManager, WireGuardError
from core.party import PartyManager
from core.utils import check_admin_rights


class LANrageTestResults:
    """Track test results"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []

    def add_pass(self, name: str, message: str = ""):
        self.passed += 1
        self.tests.append(("✓", name, message))
        print(f"   ✓ {name}")
        if message:
            print(f"     {message}")

    def add_fail(self, name: str, error: str):
        self.failed += 1
        self.tests.append(("✗", name, error))
        print(f"   ✗ {name}")
        print(f"     Error: {error}")

    def add_warning(self, name: str, message: str):
        self.warnings += 1
        self.tests.append(("⚠", name, message))
        print(f"   ⚠ {name}")
        print(f"     {message}")

    def summary(self):
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Passed:   {self.passed}")
        print(f"Failed:   {self.failed}")
        print(f"Warnings: {self.warnings}")
        print(f"Total:    {len(self.tests)}")

        if self.failed == 0:
            print("\n✅ All critical tests passed!")
            return True
        print("\n❌ Some tests failed")
        return False


@pytest.fixture
def results():
    """Pytest fixture for test results"""
    return LANrageTestResults()


@pytest.mark.asyncio
async def test_prerequisites(results):
    """Test prerequisites"""
    print("\n1. Testing Prerequisites")
    print("-" * 60)

    # Check Python version
    results.add_pass(
        "Python version",
        f"Python {sys.version_info.major}.{sys.version_info.minor}",
    )

    # Check admin rights
    has_admin = await check_admin_rights()
    if has_admin:
        results.add_pass("Admin/root privileges", "Running with elevated privileges")
    else:
        results.add_warning(
            "Admin/root privileges",
            "Not running with admin/root (required for interface creation)",
        )

    # Check config
    try:
        config = await Config.load()
        results.add_pass("Configuration", f"Loaded config (mode: {config.mode})")
    except Exception as e:
        error_msg = str(e)
        results.add_fail("Configuration", error_msg)


@pytest.mark.asyncio
async def test_wireguard(results):
    """Test WireGuard functionality"""
    print("\n2. Testing WireGuard")
    print("-" * 60)

    config = await Config.load()
    network = NetworkManager(config)

    # Test key generation
    try:
        await network._ensure_keys()
        if network.private_key and network.public_key:
            results.add_pass(
                "Key generation", f"Public key: {network.public_key_b64[:20]}..."
            )
        else:
            results.add_fail("Key generation", "Keys not generated")
    except Exception as e:
        results.add_fail("Key generation", str(e))

    # Test WireGuard installation
    try:
        wg_installed = await network._check_wireguard()
        if wg_installed:
            results.add_pass("WireGuard installation", "WireGuard found")
        else:
            results.add_fail("WireGuard installation", "WireGuard not found")
    except Exception as e:
        results.add_fail("WireGuard installation", str(e))

    # Test interface creation (only if admin)
    has_admin = await check_admin_rights()
    if has_admin and wg_installed:
        try:
            await network.initialize()
            if network.interface_created:
                results.add_pass(
                    "Interface creation", f"Interface {network.interface_name} created"
                )

                # Test interface status
                status = await network.get_interface_status()
                if status["status"] == "active":
                    results.add_pass("Interface status", "Interface is active")
                else:
                    results.add_warning(
                        "Interface status", f"Status: {status['status']}"
                    )

                # Cleanup
                await network.cleanup()
                results.add_pass("Interface cleanup", "Cleanup successful")
            else:
                results.add_fail("Interface creation", "Interface not created")
        except WireGuardError as e:
            results.add_fail("Interface creation", str(e))
        except Exception as e:
            results.add_fail("Interface creation", str(e))
    else:
        if not has_admin:
            results.add_warning("Interface creation", "Skipped (no admin rights)")
        else:
            results.add_warning(
                "Interface creation", "Skipped (WireGuard not installed)"
            )


@pytest.mark.asyncio
async def test_nat_traversal(results):
    """Test NAT traversal"""
    print("\n3. Testing NAT Traversal")
    print("-" * 60)

    config = await Config.load()
    nat = NATTraversal(config)

    # Test STUN servers
    stun_working = False
    for server, port in nat.STUN_SERVERS[:3]:
        try:
            response = await nat._stun_request((server, port))
            if response:
                results.add_pass(
                    f"STUN server {server}",
                    f"{response.public_ip}:{response.public_port}",
                )
                stun_working = True
                break
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                results.add_warning(f"STUN server {server}", "No response (timeout)")
            else:
                results.add_warning(f"STUN server {server}", f"Error: {error_msg}")

    if not stun_working:
        results.add_fail("STUN connectivity", "All STUN servers failed")
        return

    # Test NAT detection
    try:
        response = await nat.detect_nat()
        results.add_pass("NAT detection", f"Type: {response.nat_type.value}")
        results.add_pass(
            "Public endpoint", f"{response.public_ip}:{response.public_port}"
        )
        results.add_pass("Local endpoint", f"{response.local_ip}:{response.local_port}")

        # Test connection strategies
        from core.nat import NATType

        test_cases = [
            (NATType.OPEN, "Open NAT"),
            (NATType.SYMMETRIC, "Symmetric NAT"),
        ]

        for peer_nat, name in test_cases:
            strategy = nat.get_connection_strategy(peer_nat)
            results.add_pass(f"Strategy vs {name}", strategy.title())

    except NATError as e:
        results.add_fail("NAT detection", str(e))
    except Exception as e:
        error_msg = str(e)
        results.add_fail("NAT detection", error_msg)


@pytest.mark.asyncio
async def test_party_manager(results):
    """Test party management"""
    print("\n4. Testing Party Manager")
    print("-" * 60)

    config = await Config.load()
    network = NetworkManager(config)

    try:
        # Initialize network (without creating interface)
        await network._ensure_keys()

        # Create party manager
        party = PartyManager(config, network)
        results.add_pass("Party manager creation", "Manager initialized")

        # Test party creation
        test_party = await party.create_party("Test Party")
        if test_party and test_party.id:
            results.add_pass("Party creation", f"Party ID: {test_party.id}")
            results.add_pass("Party host", f"Host ID: {test_party.host_id}")
            results.add_pass("Party peers", f"Peers: {len(test_party.peers)}")
        else:
            results.add_fail("Party creation", "Failed to create party")

        # Test party status
        status = await party.get_party_status()
        if status["status"] == "in_party":
            results.add_pass("Party status", f"Status: {status['status']}")
        else:
            results.add_fail("Party status", f"Unexpected status: {status['status']}")

        # Test NAT initialization
        try:
            await party.initialize_nat()
            if party.nat:
                results.add_pass(
                    "NAT initialization", f"NAT type: {party.nat.nat_type.value}"
                )
            else:
                results.add_warning(
                    "NAT initialization", "NAT detection failed (relay-only mode)"
                )
        except Exception as e:
            results.add_warning("NAT initialization", str(e))

    except Exception as e:
        error_msg = str(e)
        results.add_fail("Party manager", error_msg)


@pytest.mark.asyncio
async def test_api_server(results):
    """Test API server (basic check)"""
    print("\n5. Testing API Server")
    print("-" * 60)

    try:
        from api.server import app

        results.add_pass("API server import", "FastAPI app loaded")

        # Check routes
        routes = [route.path for route in app.routes]
        expected_routes = [
            "/",
            "/status",
            "/party/create",
            "/party/join",
            "/party/leave",
        ]

        for route in expected_routes:
            if route in routes:
                results.add_pass(f"Route {route}", "Registered")
            else:
                results.add_fail(f"Route {route}", "Not found")

    except Exception as e:
        error_msg = str(e)
        results.add_fail("API server", error_msg)


async def main():
    """Main test runner"""
    print("🔥 LANrage Comprehensive Test Suite")
    print("=" * 60)
    print("Testing all components before Phase 2")
    print("=" * 60)

    results = LANrageTestResults()

    try:
        await test_prerequisites(results)
        await test_wireguard(results)
        await test_nat_traversal(results)
        await test_party_manager(results)
        await test_api_server(results)

        success = results.summary()

        if success:
            print("\n🎉 Ready to proceed to Phase 2!")
            print("\nNext steps:")
            print("  - Control plane implementation")
            print("  - Peer discovery protocol")
            print("  - Real P2P connections")
            print("  - Broadcast emulation")
            sys.exit(0)
        else:
            print("\n⚠️  Fix failing tests before proceeding")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
