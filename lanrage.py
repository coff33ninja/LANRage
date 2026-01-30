#!/usr/bin/env python3
"""
LANrage - Gaming VPN for the People
Main entry point
"""

import asyncio
import contextlib
import logging
import signal
import sys
from pathlib import Path

from api.server import start_api_server
from core.config import Config
from core.discord_integration import DiscordIntegration
from core.metrics import MetricsCollector
from core.network import NetworkManager, WireGuardError
from core.party import PartyManager
from core.server_browser import ServerBrowser
from core.settings import get_settings_db, init_default_settings
from core.task_manager import cancel_all_background_tasks

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global shutdown event
shutdown_event = asyncio.Event()


def shutdown_handler(signum, frame):
    """Handle shutdown signals (SIGTERM, SIGINT)"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()


async def main():
    """Main entry point"""
    logger.info("🔥 LANrage - If it runs on LAN, it runs on LANrage")

    # Register signal handlers
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    logger.info("Signal handlers registered (SIGTERM, SIGINT)")

    # Show script location for debugging
    script_dir = Path(__file__).parent.resolve()
    logger.info(f"Running from: {script_dir}")

    # Initialize settings database
    logger.info("Initializing settings database...")
    try:
        db = await get_settings_db()
        await init_default_settings()

        # Validate database integrity
        if db.validate_database_integrity():
            logger.info("Database integrity: OK")
        else:
            logger.warning("Database integrity check failed")

        db_size = db.get_database_size()
        logger.info(f"Database size: {db_size / 1024:.2f} KB")
    except Exception as e:
        logger.warning(f"Settings database initialization failed: {e}")
        logger.info("Falling back to environment variables")

    # Load config from database
    try:
        config = await Config.load_from_db()
        logger.info(f"Config loaded from database (mode: {config.mode})")
    except Exception as e:
        logger.warning(f"Failed to load from database: {e}")
        config = Config.load()
        logger.info(f"Config loaded from environment (mode: {config.mode})")

    # Initialize network manager
    network = NetworkManager(config)

    try:
        await network.initialize()
        print(f"✓ Network initialized (interface: {network.interface_name})")
    except WireGuardError as e:
        print(f"✗ Network initialization failed: {e}")
        print("\nPlease ensure:")
        print("  - WireGuard is installed")
        print("  - Running with admin/root privileges")
        print("  - No conflicting interfaces")
        sys.exit(1)

    # Initialize party manager
    party = PartyManager(config, network)
    print("✓ Party manager ready")

    # Initialize NAT traversal
    print("✓ Detecting NAT type...")
    await party.initialize_nat()

    if party.nat and party.nat.nat_type:
        print(f"  - NAT type: {party.nat.nat_type.value}")
        print(f"  - Public IP: {party.nat.public_ip}")
    else:
        print("  - NAT detection failed (relay-only mode)")

    # Initialize control plane
    print("✓ Initializing control plane...")
    await party.initialize_control()
    print("  - Control plane ready (local mode)")

    # Initialize metrics collector
    print("✓ Initializing metrics collector...")
    metrics = MetricsCollector(config)
    print("  - Metrics collector ready")

    # Initialize Discord integration
    print("✓ Initializing Discord integration...")
    discord = DiscordIntegration(config)
    logger.info("Discord integration ready")

    # Initialize server browser
    logger.info("Initializing server browser...")
    browser = ServerBrowser(config)
    logger.info("Server browser ready")

    # Start API server
    logger.info(f"Starting API server on {config.api_host}:{config.api_port}")
    logger.info(f"Open browser: http://{config.api_host}:{config.api_port}")
    logger.info(
        f"Settings page: http://{config.api_host}:{config.api_port}/settings.html"
    )

    try:
        # Create main task that can be cancelled on shutdown
        api_task = asyncio.create_task(
            start_api_server(config, party, network, metrics, discord, browser)
        )

        # Wait for either API server to complete or shutdown signal
        shutdown_task = asyncio.create_task(shutdown_event.wait())
        done, pending = await asyncio.wait(
            [api_task, shutdown_task], return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    except Exception as e:
        logger.error(f"API server error: {type(e).__name__}: {e}")
    finally:
        # Cleanup on shutdown
        logger.info("Initiating graceful shutdown...")

        try:
            # Cancel all background tasks
            logger.info("Cancelling background tasks...")
            await cancel_all_background_tasks(timeout=30)
        except Exception as e:
            logger.error(f"Error cancelling background tasks: {e}")

        try:
            # Disconnect all peers
            if party and party.connections:
                logger.info("Disconnecting all peers...")
                for peer_id in list(party.connections.keys()):
                    try:
                        await party.connections.disconnect_from_peer(peer_id)
                    except Exception as e:
                        logger.error(f"Error disconnecting peer {peer_id}: {e}")
        except Exception as e:
            logger.error(f"Error during peer cleanup: {e}")

        try:
            # Cleanup network
            logger.info("Cleaning up network...")
            await network.cleanup()
            logger.info("Network cleanup complete")
        except Exception as e:
            logger.error(f"Error during network cleanup: {e}")

        try:
            # Stop metrics
            if metrics:
                await metrics.stop()
        except Exception as e:
            logger.error(f"Error stopping metrics: {e}")

        try:
            # Disconnect Discord
            if discord:
                await discord.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting Discord: {e}")

        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("LANrage shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
