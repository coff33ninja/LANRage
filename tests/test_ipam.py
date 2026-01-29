"""Tests for IPAM module"""

import ipaddress

from core.ipam import IPAddressPool


class TestIPAddressPool:
    """Test IP address allocation and management"""

    def test_pool_initialization(self):
        """Test pool initializes with default subnet"""
        pool = IPAddressPool()
        assert pool.base_subnet == ipaddress.ip_network("10.66.0.0/16")
        assert len(pool.allocated_ips) == 0
        assert len(pool.peer_id_to_ip) == 0

    def test_single_allocation(self):
        """Test allocating a single IP"""
        pool = IPAddressPool()
        ip = pool.allocate("peer_1")

        assert ip is not None
        assert ip in pool.allocated_ips
        assert pool.get_ip("peer_1") == ip
        assert str(ip).startswith("10.66.0.")

    def test_sequential_allocation(self):
        """Test that IPs are allocated sequentially"""
        pool = IPAddressPool()

        # Allocate first 3 IPs
        ip1 = pool.allocate("peer_1")
        ip2 = pool.allocate("peer_2")
        ip3 = pool.allocate("peer_3")

        # They should be different
        assert ip1 != ip2
        assert ip2 != ip3

        # They should be in the first subnet
        assert int(ip1) >= int(ipaddress.ip_network("10.66.0.0/24").network_address) + 1
        assert (
            int(ip1) <= int(ipaddress.ip_network("10.66.0.0/24").broadcast_address) - 1
        )

    def test_duplicate_allocation(self):
        """Test that allocating same peer returns same IP"""
        pool = IPAddressPool()

        ip1 = pool.allocate("peer_1")
        ip2 = pool.allocate("peer_1")

        assert ip1 == ip2

    def test_release_and_reallocation(self):
        """Test releasing and reallocating IPs"""
        pool = IPAddressPool()

        ip_addr = pool.allocate("peer_1")
        pool.release("peer_1")

        # Released IP should be back in available pool
        assert ip_addr not in pool.allocated_ips
        assert pool.get_ip("peer_1") is None

    def test_subnet_expansion(self):
        """Test pool expands to next subnet when full"""
        pool = IPAddressPool()

        # Allocate enough IPs to fill first subnet (254 usable IPs)
        for i in range(260):
            ip = pool.allocate(f"peer_{i}")
            assert ip is not None

        # Should have used second subnet
        assert pool.current_subnet_index == 1

    def test_pool_stats(self):
        """Test pool statistics"""
        pool = IPAddressPool()

        pool.allocate("peer_1")
        pool.allocate("peer_2")

        stats = pool.get_stats()

        assert stats["allocated_count"] == 2
        assert stats["available_count"] == 252  # 254 - 2
        assert stats["total_capacity"] == 254
        assert 0 < stats["utilization_percent"] < 100

    def test_pool_validation(self):
        """Test pool validates correctly"""
        pool = IPAddressPool()

        pool.allocate("peer_1")
        pool.allocate("peer_2")

        assert pool.validate() is True

    def test_invalid_peer_release(self):
        """Test releasing non-existent peer"""
        pool = IPAddressPool()

        result = pool.release("nonexistent_peer")
        assert result is None

    def test_custom_subnet(self):
        """Test creating pool with custom subnet"""
        pool = IPAddressPool("192.168.1.0/24")

        ip = pool.allocate("peer_1")
        assert str(ip).startswith("192.168.1.")
