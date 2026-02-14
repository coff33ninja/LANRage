"""Connection management - Orchestrates peer connections"""

import asyncio
from datetime import datetime

from .config import Config
from .control import ControlPlane, PeerInfo
from .exceptions import PeerConnectionError
from .ipam import IPAddressPool
from .logging_config import get_logger, set_context, timing_decorator
from .nat import ConnectionCoordinator, NATTraversal
from .network import NetworkManager
from .task_manager import create_background_task

logger = get_logger(__name__)


class ConnectionManager:
    """Manages connections to peers"""

    def __init__(
        self,
        config: Config,
        network: NetworkManager,
        nat: NATTraversal,
        control: ControlPlane,
    ):
        self.config = config
        self.network = network
        self.nat = nat
        self.control = control
        self.coordinator = ConnectionCoordinator(config, nat)
        self.ip_pool = IPAddressPool()  # Initialize IPAM

        # Track active connections
        self.connections: dict[str, PeerConnection] = {}

    @timing_decorator(name="peer_connection")
    async def connect_to_peer(self, party_id: str, peer_id: str) -> bool:
        """
        Connect to a peer

        This orchestrates the entire connection process:
        1. Discover peer via control plane
        2. Determine connection strategy
        3. Attempt hole punching if needed
        4. Configure WireGuard peer
        5. Verify connection
        """
        set_context(party_id_val=party_id, peer_id_val=peer_id)
        logger.info(f"Starting connection to peer {peer_id} in party {party_id}")

        # Get peer info from control plane
        peer_info = await self.control.discover_peer(party_id, peer_id)
        if not peer_info:
            error_msg = f"Peer {peer_id} not found in control plane"
            logger.error(error_msg)
            raise PeerConnectionError(error_msg)

        # Determine connection strategy
        from .nat import NATType

        peer_nat_type = NATType(peer_info.nat_type)

        # Log connection attempt with NAT info
        logger.info(f"Connecting to peer {peer_id} (NAT: {peer_nat_type.value})")

        strategy_result = await self.coordinator.coordinate_connection(
            peer_info.public_key,
            {
                "nat_type": peer_info.nat_type,
                "public_ip": peer_info.public_ip,
                "public_port": peer_info.public_port,
                "local_ip": peer_info.local_ip,
                "local_port": peer_info.local_port,
            },
        )

        if not strategy_result["success"]:
            error_msg = f"Failed to determine connection strategy: {strategy_result.get('error')}"
            logger.error(error_msg)
            raise PeerConnectionError(error_msg)

        # Log selected strategy based on NAT compatibility
        logger.info(
            f"Strategy: {strategy_result['strategy']} (peer NAT: {peer_nat_type.value})"
        )

        # Configure WireGuard peer
        endpoint = strategy_result["endpoint"]

        # Assign virtual IP (simple allocation for now)
        virtual_ip = self._allocate_virtual_ip(peer_id)

        await self.network.add_peer(
            peer_public_key=peer_info.public_key,
            peer_endpoint=endpoint,
            allowed_ips=[f"{virtual_ip}/32"],
        )

        # Create connection record
        connection = PeerConnection(
            peer_id=peer_id,
            peer_info=peer_info,
            virtual_ip=virtual_ip,
            endpoint=endpoint,
            strategy=strategy_result["strategy"],
            connected_at=datetime.now(),
        )

        # Set initial state
        connection.set_status(PeerConnection.CONNECTED)

        self.connections[peer_id] = connection

        # Start monitoring connection with task manager
        create_background_task(
            self._monitor_connection(peer_id), name=f"monitor_connection_{peer_id}"
        )

        # Start cleanup task for this connection
        create_background_task(
            self._cleanup_connection(peer_id), name=f"cleanup_connection_{peer_id}"
        )

    async def disconnect_from_peer(self, peer_id: str) -> None:
        """Disconnect from a peer and clean up resources

        Args:
            peer_id: Peer ID to disconnect from
        """
        set_context(peer_id_val=peer_id)
        logger.debug(f"Initiating disconnection from peer {peer_id}")

        if peer_id not in self.connections:
            logger.warning(f"Disconnect requested for unknown peer: {peer_id}")
            return

        connection = self.connections[peer_id]

        # Remove WireGuard peer
        await self.network.remove_peer(connection.peer_info.public_key)

        # Release virtual IP back to pool
        await self._release_virtual_ip(peer_id)

        # Remove connection record
        del self.connections[peer_id]

        logger.info(f"Disconnected from peer {peer_id}")

    async def get_connection_status(self, peer_id: str) -> dict | None:
        """Get connection status for a peer"""
        set_context(peer_id_val=peer_id)

        if peer_id not in self.connections:
            logger.debug(f"Status requested for unknown peer: {peer_id}")
            return None

        connection = self.connections[peer_id]

        # Measure current latency
        latency = await self.network.measure_latency(connection.virtual_ip)

        logger.debug(
            f"Connection status for {peer_id}: {connection.status}, latency: {latency}ms"
            if latency
            else f"Connection status for {peer_id}: {connection.status}, latency: unavailable"
        )

        return {
            "peer_id": peer_id,
            "virtual_ip": connection.virtual_ip,
            "endpoint": connection.endpoint,
            "strategy": connection.strategy,
            "latency_ms": latency,
            "connected_at": connection.connected_at.isoformat(),
            "status": "connected" if latency else "degraded",
        }

    def _allocate_virtual_ip(self, peer_id: str) -> str:
        """Allocate a virtual IP for a peer using IPAM pool

        Returns:
            IPv4 address as string (e.g. "10.66.0.2")

        Raises:
            RuntimeError: If IP pool is exhausted
        """
        try:
            ip_addr = self.ip_pool.allocate(peer_id)
            return str(ip_addr)
        except RuntimeError as e:
            logger.error(f"Failed to allocate IP for peer {peer_id}: {e}")
            raise PeerConnectionError("IP pool exhausted") from e
        except ValueError as e:
            logger.error(f"Invalid IP allocation for peer {peer_id}: {e}")
            raise PeerConnectionError("IP allocation error") from e

    async def _release_virtual_ip(self, peer_id: str) -> None:
        """Release a virtual IP back to the pool

        Args:
            peer_id: Peer identifier to release IP for
        """
        try:
            released_ip = self.ip_pool.release(peer_id)
            if released_ip:
                logger.info(f"Released IP {released_ip} for peer {peer_id}")
        except Exception as e:
            logger.warning(f"Error releasing IP for peer {peer_id}: {e}")

    async def _monitor_connection(self, peer_id: str):
        """Monitor connection health"""
        set_context(peer_id_val=peer_id)
        logger.debug(f"Starting connection monitoring for peer {peer_id}")

        reconnect_attempts = 0
        max_reconnect_attempts = 3

        while peer_id in self.connections:
            await asyncio.sleep(30)  # Check every 30 seconds

            if peer_id not in self.connections:
                break

            connection = self.connections[peer_id]

            # Skip monitoring if already in cleanup
            if connection.status == PeerConnection.CLEANUP:
                break

            # Measure latency
            latency = await self.network.measure_latency(connection.virtual_ip)
            connection.last_latency = latency

            if latency is None:
                # Connection might be dead
                reconnect_attempts += 1
                logger.warning(
                    f"Connection to {peer_id} appears dead (attempt {reconnect_attempts}/{max_reconnect_attempts})"
                )

                if reconnect_attempts >= max_reconnect_attempts:
                    logger.error(
                        f"Connection to {peer_id} failed after {max_reconnect_attempts} attempts"
                    )
                    # Mark connection as failed
                    connection.set_status(PeerConnection.FAILED)
                else:
                    # Attempt reconnection
                    try:
                        logger.info(f"Attempting to reconnect to {peer_id}...")

                        # Remove old peer configuration
                        await self.network.remove_peer(connection.peer_info.public_key)

                        # Re-add peer with same configuration
                        await self.network.add_peer(
                            peer_public_key=connection.peer_info.public_key,
                            peer_endpoint=connection.endpoint,
                            allowed_ips=[f"{connection.virtual_ip}/32"],
                        )

                        # Wait a bit for connection to establish
                        await asyncio.sleep(5)

                        # Check if reconnection worked
                        new_latency = await self.network.measure_latency(
                            connection.virtual_ip
                        )
                        if new_latency:
                            logger.info(
                                f"Reconnected to {peer_id} (latency: {new_latency}ms)"
                            )
                            reconnect_attempts = 0  # Reset counter on success
                            connection.set_status(PeerConnection.CONNECTED)
                        else:
                            logger.warning("Reconnection attempt failed")

                    except Exception as e:
                        logger.error(f"Reconnection error: {type(e).__name__}: {e}")

            elif latency > 200:
                # High latency, might want to switch relay
                logger.warning(f"High latency to {peer_id}: {latency}ms")

                # Reset reconnect counter since connection is alive
                reconnect_attempts = 0
                connection.set_status(PeerConnection.DEGRADED)

                # Implement relay switching for relay connections
                if connection.strategy == "relay":
                    logger.info("Attempting to switch to a better relay server...")
                    try:
                        await self._switch_relay(peer_id, connection)
                    except Exception as e:
                        logger.warning(
                            f"Relay switching failed: {type(e).__name__}: {e}"
                        )
            else:
                # Connection is healthy
                reconnect_attempts = 0
                connection.set_status(PeerConnection.CONNECTED)

    async def _cleanup_connection(self, peer_id: str):
        """Periodically check if failed connections should be cleaned up

        Args:
            peer_id: Peer ID to monitor for cleanup
        """
        set_context(peer_id_val=peer_id)
        logger.debug(f"Starting cleanup monitoring for peer {peer_id}")

        while peer_id in self.connections:
            await asyncio.sleep(30)  # Check every 30 seconds

            if peer_id not in self.connections:
                break

            connection = self.connections[peer_id]

            # Check if this connection should be cleaned up
            if connection.should_cleanup():
                logger.info(f"Auto-cleaning up failed connection to {peer_id}")
                try:
                    await self.disconnect_from_peer(peer_id)
                except Exception as e:
                    logger.error(
                        f"Error during connection cleanup: {type(e).__name__}: {e}"
                    )
                break

    async def _switch_relay(self, peer_id: str, connection: "PeerConnection"):
        """Switch to a better relay server

        Args:
            peer_id: Peer ID to switch relay for
            connection: Current connection object
        """
        set_context(peer_id_val=peer_id)
        logger.info(f"Attempting relay switch for peer {peer_id}")

        # Get current latency for comparison
        current_latency = await self.network.measure_latency(connection.virtual_ip)
        if current_latency is None:
            logger.warning("Cannot measure current latency, aborting relay switch")
            return

        logger.debug(f"Current latency: {current_latency}ms")

        # Discover available relays
        from .nat import ConnectionCoordinator

        coordinator = ConnectionCoordinator(self.config, self.nat)

        # Get new relay endpoint
        try:
            new_relay_endpoint = await coordinator._get_relay_endpoint()

            # Check if it's different from current endpoint
            if new_relay_endpoint == connection.endpoint:
                logger.debug("Already using the best available relay")
                return

            logger.info(f"Found alternative relay: {new_relay_endpoint}")

            # Remove old peer configuration
            await self.network.remove_peer(connection.peer_info.public_key)

            # Add peer with new relay endpoint
            await self.network.add_peer(
                peer_public_key=connection.peer_info.public_key,
                peer_endpoint=new_relay_endpoint,
                allowed_ips=[f"{connection.virtual_ip}/32"],
            )

            # Wait for connection to establish
            await asyncio.sleep(3)

            # Measure new latency
            new_latency = await self.network.measure_latency(connection.virtual_ip)

            if new_latency is None:
                logger.warning("New relay failed to connect, reverting to old endpoint")
                # Revert to old endpoint
                await self.network.remove_peer(connection.peer_info.public_key)
                await self.network.add_peer(
                    peer_public_key=connection.peer_info.public_key,
                    peer_endpoint=connection.endpoint,
                    allowed_ips=[f"{connection.virtual_ip}/32"],
                )
                return

            # Compare latencies
            improvement = current_latency - new_latency
            improvement_pct = (improvement / current_latency) * 100

            if new_latency < current_latency:
                logger.info(
                    f"Switched to better relay: {new_latency}ms (improved by {improvement_pct:.1f}%)"
                )
                # Update connection with new endpoint
                connection.endpoint = new_relay_endpoint
                connection.status = "connected" if new_latency < 200 else "degraded"
            else:
                logger.warning(
                    f"New relay is slower ({new_latency}ms), reverting to original"
                )
                # Revert to old endpoint
                await self.network.remove_peer(connection.peer_info.public_key)
                await self.network.add_peer(
                    peer_public_key=connection.peer_info.public_key,
                    peer_endpoint=connection.endpoint,
                    allowed_ips=[f"{connection.virtual_ip}/32"],
                )

        except Exception as e:
            logger.error(f"Relay switching error: {type(e).__name__}: {e}")
            # Try to maintain current connection
            try:
                await self.network.add_peer(
                    peer_public_key=connection.peer_info.public_key,
                    peer_endpoint=connection.endpoint,
                    allowed_ips=[f"{connection.virtual_ip}/32"],
                )
            except OSError as e:
                # Log peer removal failures (network errors, etc.)
                logger.warning(
                    f"Failed to maintain connection after relay switch: {type(e).__name__}: {e}"
                )
            except Exception as e:
                # Catch any other unexpected errors
                logger.error(
                    f"Unexpected error maintaining connection: {type(e).__name__}: {e}"
                )


class PeerConnection:
    """Represents a connection to a peer with state management"""

    # Connection lifecycle states
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    FAILED = "failed"
    CLEANUP = "cleanup"

    VALID_STATES = {CONNECTING, CONNECTED, DEGRADED, FAILED, CLEANUP}

    def __init__(
        self,
        peer_id: str,
        peer_info: PeerInfo,
        virtual_ip: str,
        endpoint: str,
        strategy: str,
        connected_at: datetime,
    ):
        self.peer_id = peer_id
        self.peer_info = peer_info
        self.virtual_ip = virtual_ip
        self.endpoint = endpoint
        self.strategy = strategy
        self.connected_at = connected_at
        self.status = self.CONNECTING
        self.last_latency: float | None = None
        self.failed_at: datetime | None = None
        self.cleanup_timeout = 300  # 5 minutes before auto-cleanup

    def set_status(self, new_status: str) -> bool:
        """Set connection status with validation"""
        if new_status not in self.VALID_STATES:
            logger.error(f"Invalid connection status: {new_status}")
            return False

        old_status = self.status
        self.status = new_status
        logger.info(f"Peer {self.peer_id}: {old_status} -> {new_status}")

        if new_status == self.FAILED:
            self.failed_at = datetime.now()

        return True

    def should_cleanup(self) -> bool:
        """Check if connection should be cleaned up"""
        if self.status != self.FAILED or not self.failed_at:
            return False

        elapsed = (datetime.now() - self.failed_at).total_seconds()
        return elapsed > self.cleanup_timeout
