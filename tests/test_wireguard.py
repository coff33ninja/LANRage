#!/usr/bin/env python3
"""
Test script for WireGuard functionality
Run this to verify WireGuard is working
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.network import NetworkManager, WireGuardError
from core.utils import check_admin_rights


@pytest.mark.asyncio
async def test_wireguard():
    """Test WireGuard setup"""
    print("🔥 LANrage WireGuard Test")
    print("=" * 60)

    # Check admin rights
    print("\n1. Checking admin/root privileges...")
    has_admin = await check_admin_rights()
    if has_admin:
        print("   ✓ Running with admin/root privileges")
    else:
        print("   ⚠ Not running with admin/root privileges")
        print("   Note: Required for interface creation")

    # Load config
    print("\n2. Loading configuration...")
    config = Config.load()
    print("   ✓ Config loaded")
    print(f"   - Mode: {config.mode}")
    print(f"   - Interface: {config.interface_name}")
    print(f"   - Subnet: {config.virtual_subnet}")

    # Initialize network manager
    print("\n3. Initializing network manager...")
    network = NetworkManager(config)

    try:
        await network.initialize()
        print("   ✓ Network manager initialized")
        print(f"   - Public key: {network.public_key_b64[:20]}...")
        print(f"   - Interface created: {network.interface_created}")

    except WireGuardError as e:
        error_msg = str(e)
        print(f"   ✗ Failed to initialize: {error_msg}")
        return False

    # Get interface status
    print("\n4. Checking interface status...")
    status = await network.get_interface_status()
    if status["status"] == "active":
        print("   ✓ Interface is active")
        print(f"   - Interface: {status['interface']}")
        print(f"   - Public key: {status['public_key'][:20]}...")
    else:
        print(f"   ✗ Interface status: {status['status']}")
        if "error" in status:
            print(f"   Error: {status['error']}")

    # Test latency measurement
    print("\n5. Testing latency measurement...")
    latency = await network.measure_latency("8.8.8.8")
    if latency:
        print(f"   ✓ Latency to 8.8.8.8: {latency}ms")
    else:
        print("   ⚠ Could not measure latency")

    # Cleanup
    print("\n6. Cleaning up...")
    await network.cleanup()
    print("   ✓ Cleanup complete")

    print("\n" + "=" * 60)
    print("✅ WireGuard test complete!")
    return True


async def main():
    """Main entry point"""
    try:
        success = await test_wireguard()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
