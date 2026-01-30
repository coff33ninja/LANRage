"""IP Address Management for LANrage virtual network"""

import ipaddress
import logging

logger = logging.getLogger(__name__)


class IPAddressPool:
    """Manages allocation and deallocation of IP addresses from a subnet

    Features:
    - Sequential allocation to minimize collisions
    - Proper subnet validation (reserves .0 and .255)
    - Tracking of allocated/available IPs
    - Automatic expansion to next subnet when full
    """

    def __init__(self, base_subnet: str = "10.66.0.0/16"):
        """Initialize IP pool

        Args:
            base_subnet: Base subnet in CIDR notation (e.g. "10.66.0.0/16")
        """
        self.base_subnet = ipaddress.ip_network(base_subnet)
        self.allocated_ips: set[ipaddress.IPv4Address] = set()
        self.peer_id_to_ip: dict[str, ipaddress.IPv4Address] = {}
        self.current_subnet_index = 0

        logger.info(f"IPAM initialized with base subnet: {self.base_subnet}")

    def _get_subnet(self, index: int = 0) -> ipaddress.ip_network:
        """Get a /24 subnet from the base network

        Args:
            index: Subnet index (0 is 10.66.0.0/24, 1 is 10.66.1.0/24, etc.)

        Returns:
            IPv4Network for the requested subnet
        """
        # Extract network and calculate offset
        network_int = int(self.base_subnet.network_address)
        # Each /24 subnet is 256 addresses apart
        subnet_int = network_int + (index * 256)

        subnet = ipaddress.ip_network((subnet_int, 24), strict=False)

        # Validate subnet is within base network
        if not subnet.subnet_of(self.base_subnet):
            raise ValueError(f"Subnet {subnet} exceeds base network {self.base_subnet}")

        return subnet

    def allocate(self, peer_id: str) -> ipaddress.IPv4Address:
        """Allocate an IP address for a peer

        Args:
            peer_id: Unique peer identifier

        Returns:
            Allocated IPv4Address

        Raises:
            RuntimeError: If no IPs available in pool
            ValueError: If peer_id already allocated
        """
        # Check if already allocated
        if peer_id in self.peer_id_to_ip:
            ip = self.peer_id_to_ip[peer_id]
            logger.warning(f"Peer {peer_id} already allocated IP {ip}")
            return ip

        # Find available IP in current subnet
        subnet = self._get_subnet(self.current_subnet_index)

        for ip_addr in subnet.hosts():  # Skips .0 and .255 automatically
            if ip_addr not in self.allocated_ips:
                # Allocate this IP
                self.allocated_ips.add(ip_addr)
                self.peer_id_to_ip[peer_id] = ip_addr
                logger.info(f"Allocated IP {ip_addr} to peer {peer_id}")
                return ip_addr

        # Current subnet is full, try next subnet
        logger.info(f"Subnet {subnet} is full, expanding to next subnet")
        self.current_subnet_index += 1

        # Check if we've exceeded subnet capacity
        if self.current_subnet_index >= 256:  # Max /24 subnets in /16
            raise RuntimeError(
                f"IP pool exhausted: cannot allocate more than {256 * 254} addresses"
            )

        # Recursively try next subnet
        return self.allocate(peer_id)

    def release(self, peer_id: str) -> ipaddress.IPv4Address | None:
        """Release an IP address back to the pool

        Args:
            peer_id: Peer identifier to release

        Returns:
            Released IPv4Address or None if not found
        """
        if peer_id not in self.peer_id_to_ip:
            logger.warning(f"Peer {peer_id} not found in allocation table")
            return None

        ip = self.peer_id_to_ip[peer_id]
        self.allocated_ips.discard(ip)
        del self.peer_id_to_ip[peer_id]

        logger.info(f"Released IP {ip} from peer {peer_id}")
        return ip

    def get_ip(self, peer_id: str) -> ipaddress.IPv4Address | None:
        """Get the allocated IP for a peer

        Args:
            peer_id: Peer identifier

        Returns:
            IPv4Address if allocated, None otherwise
        """
        return self.peer_id_to_ip.get(peer_id)

    def get_stats(self) -> dict:
        """Get pool statistics

        Returns:
            Dictionary with allocation stats
        """
        total_capacity = (
            self.current_subnet_index + 1
        ) * 254  # /24 subnet - reserved IPs

        return {
            "base_subnet": str(self.base_subnet),
            "current_subnet_index": self.current_subnet_index,
            "allocated_count": len(self.allocated_ips),
            "available_count": total_capacity - len(self.allocated_ips),
            "total_capacity": total_capacity,
            "utilization_percent": (
                (len(self.allocated_ips) / total_capacity * 100)
                if total_capacity > 0
                else 0
            ),
        }

    def validate(self) -> bool:
        """Validate pool integrity

        Returns:
            True if pool is valid, False otherwise
        """
        # Check that all allocated IPs are within subnets
        max_subnet_index = self.current_subnet_index

        for peer_id, ip_addr in self.peer_id_to_ip.items():
            # Get subnet index from IP
            network_int = int(self.base_subnet.network_address)
            ip_int = int(ip_addr)
            subnet_index = (ip_int - network_int) // 256

            if subnet_index > max_subnet_index:
                logger.error(
                    f"Invalid IP allocation: {ip_addr} in subnet {subnet_index} "
                    f"but max is {max_subnet_index}"
                )
                return False

            # Verify IP is in the subnet
            subnet = self._get_subnet(subnet_index)
            if ip_addr not in subnet:
                logger.error(f"IP {ip_addr} not in subnet {subnet}")
                return False

        logger.info("IPAM validation passed")
        return True
