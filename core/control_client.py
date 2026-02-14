"""
Remote Control Plane Client - HTTP-based client for centralized control plane

Uses httpx for robust async HTTP communication with:
- Automatic retries
- Connection pooling
- Timeout handling
- Proper error handling
"""

import asyncio
import contextlib

import httpx

from .config import Config
from .control import ControlPlaneError, PartyInfo, PeerInfo
from .logging_config import get_logger, set_context, timing_decorator

logger = get_logger(__name__)


class RemoteControlPlaneClient:
    """
    HTTP-based client for remote control plane server

    Features:
    - Async HTTP requests with httpx
    - Automatic retry logic
    - Connection pooling
    - Timeout handling
    - Heartbeat management
    """

    def __init__(self, config: Config):
        self.config = config
        self.server_url = config.control_server
        self.client: httpx.AsyncClient | None = None
        self.auth_token: str | None = None
        self.my_peer_id: str | None = None
        self.my_party_id: str | None = None

        # Heartbeat task
        self.heartbeat_task: asyncio.Task | None = None
        self.heartbeat_interval = 30  # seconds

    @timing_decorator(name="control_client_init")
    async def initialize(self):
        """Initialize the client"""
        logger.info(f"Initializing control plane client: {self.server_url}")
        # Create httpx client with connection pooling and timeouts
        self.client = httpx.AsyncClient(
            base_url=self.server_url,
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            follow_redirects=True,
        )
        logger.info(f"Control plane client initialized successfully: {self.server_url}")

    @timing_decorator(name="control_client_close")
    async def close(self):
        """Close the client and cleanup"""
        logger.info("Closing control plane client")
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.heartbeat_task
            self.heartbeat_task = None

        if self.client:
            await self.client.aclose()
            self.client = None
        logger.debug("Control plane client closed")

    @timing_decorator(name="control_client_request")
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict | None = None,
        retry_count: int = 3,
    ) -> dict:
        """Make HTTP request with retry logic

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint
            json_data: JSON data to send
            retry_count: Number of retries on failure

        Returns:
            Response JSON data

        Raises:
            ControlPlaneError: On request failure
        """
        if not self.client:
            logger.error("Control plane client not initialized")
            raise ControlPlaneError("Client not initialized")

        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        for attempt in range(retry_count):
            try:
                logger.debug(
                    f"Making {method} request to {endpoint} (attempt {attempt + 1})"
                )
                response = await self.client.request(
                    method=method,
                    url=endpoint,
                    json=json_data,
                    headers=headers,
                )

                # Check for HTTP errors
                if response.status_code >= 400:
                    error_detail = response.json().get("detail", "Unknown error")
                    logger.warning(f"HTTP {response.status_code}: {error_detail}")
                    raise ControlPlaneError(
                        f"HTTP {response.status_code}: {error_detail}"
                    )

                logger.debug(f"Request successful: {method} {endpoint}")
                return response.json()

            except httpx.TimeoutException:
                if attempt < retry_count - 1:
                    logger.warning(f"Request timeout, retrying (attempt {attempt + 1})")
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                    continue
                logger.error("Request timeout - max retries exceeded")
                raise ControlPlaneError("Request timeout") from None

            except httpx.ConnectError as e:
                if attempt < retry_count - 1:
                    logger.warning(
                        f"Connection failed: {e}, retrying (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                logger.error(f"Connection failed - max retries exceeded: {e}")
                raise ControlPlaneError(f"Connection failed: {e}") from None

            except httpx.HTTPError as e:
                if attempt < retry_count - 1:
                    logger.warning(f"HTTP error: {e}, retrying (attempt {attempt + 1})")
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                logger.error(f"HTTP error - max retries exceeded: {e}")
                raise ControlPlaneError(f"HTTP error: {e}") from None

            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise ControlPlaneError(f"Request failed: {e}") from e

        logger.error("Max retries exceeded")
        raise ControlPlaneError("Max retries exceeded")

    @timing_decorator(name="control_register_peer")
    async def register_peer(self, peer_id: str) -> str:
        """
        Register peer and get authentication token

        Args:
            peer_id: Unique peer identifier

        Returns:
            Authentication token
        """
        try:
            set_context(peer_id_val=peer_id)
            logger.info(f"Registering peer with control plane: {peer_id}")
            response = await self._request(
                "POST",
                f"/auth/register?peer_id={peer_id}",
                retry_count=3,
            )

            self.auth_token = response["token"]
            self.my_peer_id = peer_id

            logger.info(f"Peer registered successfully: {peer_id}")
            return self.auth_token

        except Exception as e:
            logger.error(f"Failed to register peer: {e}")
            raise ControlPlaneError(f"Failed to register peer: {e}") from e

    @timing_decorator(name="control_register_party")
    async def register_party(
        self, party_id: str, name: str, host_peer_info: PeerInfo
    ) -> PartyInfo:
        """
        Register a new party

        Args:
            party_id: Party identifier
            name: Party name
            host_peer_info: Host peer information

        Returns:
            Created party information
        """
        try:
            set_context(party_id_val=party_id)
            logger.info(
                f"Registering party with control plane: {name} (ID: {party_id})"
            )
            response = await self._request(
                "POST",
                "/parties",
                json_data={
                    "name": name,
                    "host_peer_info": host_peer_info.to_dict(),
                },
            )

            party = PartyInfo.from_dict(response["party"])
            self.my_party_id = party.party_id

            # Start heartbeat
            await self._start_heartbeat()

            logger.info(f"Party registered successfully: {name} (ID: {party.party_id})")
            return party

        except Exception as e:
            logger.error(f"Failed to register party: {e}")
            raise ControlPlaneError(f"Failed to register party: {e}") from e

    @timing_decorator(name="control_join_party")
    async def join_party(self, party_id: str, peer_info: PeerInfo) -> PartyInfo:
        """
        Join an existing party

        Args:
            party_id: Party to join
            peer_info: Peer information

        Returns:
            Party information
        """
        try:
            set_context(party_id_val=party_id)
            logger.info(f"Joining party with control plane: {party_id}")
            response = await self._request(
                "POST",
                f"/parties/{party_id}/join",
                json_data={
                    "party_id": party_id,
                    "peer_info": peer_info.to_dict(),
                },
            )

            party = PartyInfo.from_dict(response["party"])
            self.my_party_id = party_id

            # Start heartbeat
            await self._start_heartbeat()

            logger.info(f"Joined party successfully: {party.name} (ID: {party_id})")
            return party

        except Exception as e:
            logger.error(f"Failed to join party: {e}")
            raise ControlPlaneError(f"Failed to join party: {e}") from e

    async def leave_party(self, party_id: str, peer_id: str):
        """
        Leave a party

        Args:
            party_id: Party to leave
            peer_id: Peer leaving
        """
        try:
            # Stop heartbeat
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                self.heartbeat_task = None

            await self._request(
                "DELETE",
                f"/parties/{party_id}/peers/{peer_id}",
            )

            if self.my_party_id == party_id:
                self.my_party_id = None

            print("✓ Left party")

        except Exception as e:
            raise ControlPlaneError(f"Failed to leave party: {e}") from e

    async def get_party(self, party_id: str) -> PartyInfo | None:
        """
        Get party information

        Args:
            party_id: Party identifier

        Returns:
            Party information or None if not found
        """
        try:
            response = await self._request("GET", f"/parties/{party_id}")
            return PartyInfo.from_dict(response["party"])

        except ControlPlaneError as e:
            if "404" in str(e):
                return None
            raise

    async def get_peers(self, party_id: str) -> dict[str, PeerInfo]:
        """
        Get all peers in a party

        Args:
            party_id: Party identifier

        Returns:
            Dictionary of peer_id -> PeerInfo
        """
        try:
            response = await self._request("GET", f"/parties/{party_id}/peers")
            return {k: PeerInfo.from_dict(v) for k, v in response["peers"].items()}

        except Exception as e:
            raise ControlPlaneError(f"Failed to get peers: {e}") from e

    async def discover_peer(self, party_id: str, peer_id: str) -> PeerInfo | None:
        """
        Discover a specific peer

        Args:
            party_id: Party identifier
            peer_id: Peer to discover

        Returns:
            Peer information or None if not found
        """
        try:
            response = await self._request(
                "GET", f"/parties/{party_id}/peers/{peer_id}"
            )
            return PeerInfo.from_dict(response["peer"])

        except ControlPlaneError as e:
            if "404" in str(e):
                return None
            raise

    async def heartbeat(self, party_id: str, peer_id: str):
        """
        Send heartbeat to keep peer alive

        Args:
            party_id: Party identifier
            peer_id: Peer identifier
        """
        try:
            await self._request(
                "POST",
                f"/parties/{party_id}/peers/{peer_id}/heartbeat",
            )

        except Exception as e:
            # Don't raise on heartbeat failure, just log
            print(f"⚠️  Heartbeat failed: {e}")

    async def list_relays(self) -> list[dict]:
        """
        List available relay servers

        Returns:
            List of relay server information
        """
        try:
            response = await self._request("GET", "/relays")
            return response["relays"]

        except Exception as e:
            raise ControlPlaneError(f"Failed to list relays: {e}") from e

    async def get_relays_by_region(self, region: str) -> list[dict]:
        """
        Get relay servers in a specific region

        Args:
            region: Region name

        Returns:
            List of relay servers in region
        """
        try:
            response = await self._request("GET", f"/relays/{region}")
            return response["relays"]

        except Exception as e:
            raise ControlPlaneError(f"Failed to get relays: {e}") from e

    async def _start_heartbeat(self):
        """Start heartbeat task"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()

        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self):
        """Heartbeat loop to keep connection alive"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                if self.my_party_id and self.my_peer_id:
                    await self.heartbeat(self.my_party_id, self.my_peer_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️  Heartbeat error: {e}")
                # Continue heartbeat loop even on error


def create_control_plane_client(config: Config) -> RemoteControlPlaneClient:
    """
    Factory function to create control plane client

    Args:
        config: Configuration

    Returns:
        Control plane client instance
    """
    return RemoteControlPlaneClient(config)
