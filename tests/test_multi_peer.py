#!/usr/bin/env python3
"""
Multi-peer test script
Simulates multiple peers connecting to test the full system
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime

from core.config import Config
from core.control import LocalControlPlane, PeerInfo
from core.nat import NATTraversal
from core.network import NetworkManager
from core.party import PartyManager


class LANrageTestPeer:
    """A test peer"""

    def __init__(self, peer_id: str, name: str):
        self.peer_id = peer_id
        self.name = name
        self.config = None  # Will be loaded async
        self.network = None
        self.nat = None
        self.control = None
        self.party_manager = None
        # Store creation time using datetime for tracking
        self.created_at = datetime.now()
        # PeerInfo will be used when control plane is fully implemented
        self.peer_info: PeerInfo | None = None

    async def initialize(self):
        """Initialize peer"""
        print(f"\n[{self.name}] Initializing...")

        # Load config
        self.config = await Config.load()

        # Initialize network (without creating interface for testing)
        self.network = NetworkManager(self.config)
        await self.network._ensure_keys()
        print(f"[{self.name}] ✓ Keys generated")

        # Initialize NAT
        self.nat = NATTraversal(self.config)
        try:
            await self.nat.detect_nat()
            print(f"[{self.name}] ✓ NAT detected: {self.nat.nat_type.value}")
        except Exception:
            print(f"[{self.name}] ⚠ NAT detection failed")

        # Initialize control plane
        self.control = LocalControlPlane(self.config)
        await self.control.initialize()
        print(f"[{self.name}] ✓ Control plane ready")

        # Initialize party manager
        self.party_manager = PartyManager(self.config, self.network)
        self.party_manager.my_peer_id = self.peer_id
        self.party_manager.nat = self.nat
        self.party_manager.control = self.control
        print(f"[{self.name}] ✓ Party manager ready")

    async def create_party(self, party_name: str) -> str:
        """Create a party"""
        print(f"\n[{self.name}] Creating party: {party_name}")

        party = await self.party_manager.create_party(party_name)
        print(f"[{self.name}] ✓ Party created: {party.id}")

        return party.id

    async def join_party(self, party_id: str):
        """Join a party"""
        print(f"\n[{self.name}] Joining party: {party_id}")

        try:
            party = await self.party_manager.join_party(party_id, self.name)
            print(f"[{self.name}] ✓ Joined party")
            print(f"[{self.name}]   Peers in party: {len(party.peers)}")
        except Exception as e:
            print(f"[{self.name}] ✗ Failed to join: {e}")

    async def get_status(self):
        """Get party status"""
        status = await self.party_manager.get_party_status()

        if status["status"] == "in_party":
            print(f"\n[{self.name}] Party Status:")
            print(f"  Party ID: {status['party']['id']}")
            print(f"  Peers: {status['peer_count']}")

            for peer in status["party"]["peers"].values():
                print(f"    - {peer['name']} ({peer['connection_type']})")
        else:
            print(f"\n[{self.name}] Not in party")


@pytest.mark.asyncio
async def test_two_peers():
    """Test with two peers"""
    print("🔥 LANrage Multi-Peer Test: 2 Peers")
    print("=" * 60)

    # Create peers
    peer1 = LANrageTestPeer("peer_001", "Alice")
    peer2 = LANrageTestPeer("peer_002", "Bob")

    # Initialize both
    await peer1.initialize()
    await peer2.initialize()

    # Peer 1 creates party
    party_id = await peer1.create_party("Test Party")

    # Wait a bit
    await asyncio.sleep(1)

    # Peer 2 joins party
    await peer2.join_party(party_id)

    # Wait a bit
    await asyncio.sleep(1)

    # Check status
    await peer1.get_status()
    await peer2.get_status()

    print("\n" + "=" * 60)
    print("✅ Two-peer test complete!")


@pytest.mark.asyncio
async def test_three_peers():
    """Test with three peers"""
    print("🔥 LANrage Multi-Peer Test: 3 Peers")
    print("=" * 60)

    # Create peers
    peer1 = LANrageTestPeer("peer_001", "Alice")
    peer2 = LANrageTestPeer("peer_002", "Bob")
    peer3 = LANrageTestPeer("peer_003", "Charlie")

    # Initialize all
    await peer1.initialize()
    await peer2.initialize()
    await peer3.initialize()

    # Peer 1 creates party
    party_id = await peer1.create_party("Test Party")

    # Wait a bit
    await asyncio.sleep(1)

    # Peer 2 and 3 join
    await peer2.join_party(party_id)
    await asyncio.sleep(0.5)
    await peer3.join_party(party_id)

    # Wait a bit
    await asyncio.sleep(1)

    # Check status
    await peer1.get_status()
    await peer2.get_status()
    await peer3.get_status()

    print("\n" + "=" * 60)
    print("✅ Three-peer test complete!")


@pytest.mark.asyncio
async def test_party_discovery():
    """Test party discovery"""
    print("🔥 LANrage Multi-Peer Test: Party Discovery")
    print("=" * 60)

    # Create peer
    peer1 = LANrageTestPeer("peer_001", "Alice")
    await peer1.initialize()

    # Create multiple parties
    party1_id = await peer1.create_party("Gaming Session 1")
    print(f"[Discovery] Party 1 created: {party1_id}")
    await asyncio.sleep(0.5)

    peer2 = LANrageTestPeer("peer_002", "Bob")
    await peer2.initialize()
    party2_id = await peer2.create_party("Gaming Session 2")
    print(f"[Discovery] Party 2 created: {party2_id}")

    # Wait a bit
    await asyncio.sleep(1)

    # Discover parties
    print("\n[Discovery] Discovering parties...")
    parties = await peer1.control.discover_parties()

    print(f"[Discovery] Found {len(parties)} parties:")
    for party_id, party in parties.items():
        print(f"  - {party.name} ({party_id})")
        print(f"    Host: {party.host_id}")
        print(f"    Peers: {len(party.peers)}")

    print("\n" + "=" * 60)
    print("✅ Party discovery test complete!")


async def main():
    """Main test runner"""
    print("Select test:")
    print("1. Two peers")
    print("2. Three peers")
    print("3. Party discovery")
    print("4. All tests")

    choice = input("\nChoice (1-4): ").strip()

    try:
        if choice == "1":
            await test_two_peers()
        elif choice == "2":
            await test_three_peers()
        elif choice == "3":
            await test_party_discovery()
        elif choice == "4":
            await test_two_peers()
            print("\n")
            await test_three_peers()
            print("\n")
            await test_party_discovery()
        else:
            print("Invalid choice")
            sys.exit(1)

        print("\n🎉 All tests passed!")

    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
