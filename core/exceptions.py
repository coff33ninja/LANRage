"""Custom exceptions for LANrage"""


class LANrageError(Exception):
    """Base exception for all LANrage errors"""

    pass


class NATError(LANrageError):
    """NAT detection or traversal failure"""

    pass


class STUNError(NATError):
    """STUN protocol error"""

    pass


class HolePunchError(NATError):
    """UDP hole punching failure"""

    pass


class ConnectionError(LANrageError):
    """Connection establishment or management error"""

    pass


class PeerConnectionError(ConnectionError):
    """Error connecting to a specific peer"""

    pass


class ReconnectionFailedError(ConnectionError):
    """Reconnection attempt failed after max retries"""

    pass


class ConfigError(LANrageError):
    """Configuration loading or validation error"""

    pass


class DatabaseConfigError(ConfigError):
    """Database configuration loading error"""

    pass


class BroadcastError(LANrageError):
    """Broadcast emulation error"""

    pass


class SocketError(BroadcastError):
    """Socket creation or binding error"""

    pass


class WireGuardError(LANrageError):
    """WireGuard configuration or operation error"""

    pass


class NetworkError(LANrageError):
    """Network operation error"""

    pass


class PartyError(LANrageError):
    """Party management error"""

    pass


class PartyNotFoundError(PartyError):
    """Party does not exist"""

    pass


class PeerNotFoundError(PartyError):
    """Peer does not exist in party"""

    pass
