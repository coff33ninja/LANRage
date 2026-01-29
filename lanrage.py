#!/usr/bin/env python3
"""
LANrage - Gaming VPN for the People
Main entry point
"""

import asyncio
import sys
from pathlib import Path

from core.config import Config
from core.network import NetworkManager
from core.party import PartyManager
from api.server import start_api_server


async def main():
    """Main entry point"""
    print("🔥 LANrage - If it runs on LAN, it runs on LANrage")
    print("=" * 60)
    
    # Load config
    config = Config.load()
    print(f"✓ Config loaded (mode: {config.mode})")
    
    # Initialize network manager
    network = NetworkManager(config)
    await network.initialize()
    print(f"✓ Network initialized (interface: {network.interface_name})")
    
    # Initialize party manager
    party = PartyManager(config, network)
    print("✓ Party manager ready")
    
    # Start API server
    print(f"✓ Starting API server on {config.api_host}:{config.api_port}")
    await start_api_server(config, party, network)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 LANrage shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
