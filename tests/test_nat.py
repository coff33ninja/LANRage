#!/usr/bin/env python3
"""
Test script for NAT traversal functionality
Run this to verify STUN and hole punching work
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.nat import NATError, NATTraversal, NATType


@pytest.mark.asyncio
async def test_nat_traversal():
    """Test NAT traversal"""
    print("🔥 LANrage NAT Traversal Test")
    print("=" * 60)

    # Load config
    config = await Config.load()

    # Initialize NAT traversal
    print("\n1. Detecting NAT type...")
    nat = NATTraversal(config)

    try:
        response = await nat.detect_nat()
        print("   ✓ NAT detected")
        print(f"   - Type: {response.nat_type.value}")
        print(f"   - Public IP: {response.public_ip}")
        print(f"   - Public Port: {response.public_port}")
        print(f"   - Local IP: {response.local_ip}")
        print(f"   - Local Port: {response.local_port}")

    except NATError as e:
        error_msg = str(e)
        print(f"   ✗ Failed to detect NAT: {error_msg}")
        return False

    # Test STUN servers
    print("\n2. Testing STUN servers...")
    for server, port in nat.STUN_SERVERS[:3]:
        try:
            result = await nat._stun_request((server, port))
            if result:
                print(f"   ✓ {server}:{port} - OK")
            else:
                print(f"   ⚠ {server}:{port} - No response")
        except Exception as e:
            error_msg = str(e)
            print(f"   ✗ {server}:{port} - Failed: {error_msg}")

    # Test connection strategies
    print("\n3. Connection strategy analysis...")

    test_cases = [
        (NATType.OPEN, "Open NAT"),
        (NATType.FULL_CONE, "Full Cone"),
        (NATType.RESTRICTED_CONE, "Restricted Cone"),
        (NATType.PORT_RESTRICTED_CONE, "Port-Restricted Cone"),
        (NATType.SYMMETRIC, "Symmetric"),
    ]

    for peer_nat, name in test_cases:
        can_direct = nat.can_direct_connect(peer_nat)
        strategy = nat.get_connection_strategy(peer_nat)

        emoji = "✓" if can_direct else "⚠"

        print(f"   - vs {name}: {strategy.title()} {emoji}")

    # Summary
    print("\n4. NAT Summary...")
    print(f"   - Your NAT type: {nat.nat_type.value}")

    if nat.nat_type == NATType.OPEN:
        print("   - ✓ Best case: Direct connections to all peers")
    elif nat.nat_type in (
        NATType.FULL_CONE,
        NATType.RESTRICTED_CONE,
        NATType.PORT_RESTRICTED_CONE,
    ):
        print("   - ✓ Good: Direct connections with hole punching")
        print("   - ⚠ Symmetric NAT peers will need relay")
    elif nat.nat_type == NATType.SYMMETRIC:
        print("   - ⚠ Difficult: Most connections will need relay")
        print("   - Consider using different network or VPN")
    else:
        print("   - ❓ Unknown NAT type")

    print("\n" + "=" * 60)
    print("✅ NAT traversal test complete!")
    return True


async def main():
    """Main entry point"""
    try:
        success = await test_nat_traversal()
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
