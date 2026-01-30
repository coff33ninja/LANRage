"""Metrics collection and statistics tracking"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field

import psutil

from .config import Config


@dataclass
class MetricPoint:
    """A single metric data point"""

    timestamp: float
    value: float


@dataclass
class PeerMetrics:
    """Metrics for a specific peer"""

    peer_id: str
    peer_name: str
    latency: deque[MetricPoint] = field(default_factory=lambda: deque(maxlen=360))
    bytes_sent: int = 0
    bytes_received: int = 0
    packets_sent: int = 0
    packets_received: int = 0
    connection_uptime: float = 0
    last_seen: float = field(default_factory=time.time)
    status: str = "connected"  # "connected", "degraded", "disconnected"

    # Connection quality tracking
    packet_loss_percent: float = 0.0
    jitter_ms: float = 0.0
    quality_score: float = 100.0  # 0-100 score
    quality_trend: str = "stable"  # "improving", "stable", "degrading"


@dataclass
class SystemMetrics:
    """System-level metrics"""

    cpu_percent: deque[MetricPoint] = field(default_factory=lambda: deque(maxlen=360))
    memory_percent: deque[MetricPoint] = field(
        default_factory=lambda: deque(maxlen=360)
    )
    network_sent: deque[MetricPoint] = field(default_factory=lambda: deque(maxlen=360))
    network_received: deque[MetricPoint] = field(
        default_factory=lambda: deque(maxlen=360)
    )


def predict_connection_quality(
    latency_ms: float,
    packet_loss_percent: float = 0.0,
    jitter_ms: float = 0.0,
) -> tuple[float, str]:
    """Predict connection quality based on network metrics

    Uses a weighted scoring algorithm to compute connection quality (0-100).
    Factors:
    - Latency (40%): Lower is better. 0ms=100pts, 150ms=0pts
    - Packet Loss (35%): 0% loss=100pts, 5% loss=0pts
    - Jitter (25%): Lower variance is better. 0ms=100pts, 50ms=0pts

    Args:
        latency_ms: Round-trip latency in milliseconds
        packet_loss_percent: Packet loss percentage (0-100)
        jitter_ms: Jitter (standard deviation of latency) in milliseconds

    Returns:
        Tuple of (quality_score: float, quality_status: str)
        - quality_score: 0-100 score
        - quality_status: "excellent", "good", "fair", "poor"
    """
    # Latency score: 100 at 0ms, 0 at 150ms (linear)
    latency_score = max(0, 100 - (latency_ms / 1.5))

    # Packet loss score: 100 at 0%, 0 at 5%
    loss_score = max(0, 100 - (packet_loss_percent * 20))

    # Jitter score: 100 at 0ms, 0 at 50ms
    jitter_score = max(0, 100 - (jitter_ms * 2))

    # Weighted average (latency is most critical for gaming)
    quality_score = latency_score * 0.40 + loss_score * 0.35 + jitter_score * 0.25

    # Determine quality status
    if quality_score >= 80:
        status = "excellent"
    elif quality_score >= 60:
        status = "good"
    elif quality_score >= 40:
        status = "fair"
    else:
        status = "poor"

    return quality_score, status


def aggregate_metrics_by_window(
    metrics: list[MetricPoint],
    window_seconds: float = 60.0,
    current_time: float | None = None,
) -> dict:
    """Aggregate metrics by time window using statistical measures

    Reduces data volume by aggregating raw metrics into statistical summaries
    within time windows. This is useful for long-term trending analysis.

    Args:
        metrics: List of MetricPoint data to aggregate
        window_seconds: Time window size in seconds
        current_time: Current time (defaults to now)

    Returns:
        Dictionary with aggregated statistics:
        - count: Number of data points in window
        - min: Minimum value
        - max: Maximum value
        - avg: Average value
        - p95: 95th percentile
        - sum: Sum of values
    """
    if not metrics:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "avg": None,
            "p95": None,
            "sum": 0,
        }

    if current_time is None:
        current_time = time.time()

    cutoff_time = current_time - window_seconds

    # Filter metrics within window
    window_values = [m.value for m in metrics if m.timestamp >= cutoff_time]

    if not window_values:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "avg": None,
            "p95": None,
            "sum": 0,
        }

    # Calculate statistics
    sorted_values = sorted(window_values)
    count = len(sorted_values)

    # 95th percentile
    p95_index = int(count * 0.95)
    p95 = sorted_values[p95_index] if p95_index < count else sorted_values[-1]

    return {
        "count": count,
        "min": min(sorted_values),
        "max": max(sorted_values),
        "avg": sum(sorted_values) / count,
        "p95": p95,
        "sum": sum(sorted_values),
    }


@dataclass
class GameSession:
    """A game session record"""

    game_id: str
    game_name: str
    started_at: float
    ended_at: float | None = None
    duration: float | None = None
    peers: list[str] = field(default_factory=list)
    avg_latency: float | None = None
    max_latency: float | None = None
    min_latency: float | None = None


class MetricsCollector:
    """Collects and stores metrics for monitoring"""

    def __init__(self, config: Config):
        self.config = config
        self.running = False

        # Peer metrics
        self.peer_metrics: dict[str, PeerMetrics] = {}

        # System metrics
        self.system_metrics = SystemMetrics()

        # Game sessions
        self.game_sessions: deque[GameSession] = deque(maxlen=100)
        self.active_session: GameSession | None = None

        # Network baseline (for calculating delta)
        self.network_baseline = None

        # Collection interval (seconds)
        self.collection_interval = 10

    async def start(self):
        """Start metrics collection"""
        self.running = True

        # Get network baseline
        net_io = psutil.net_io_counters()
        self.network_baseline = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "timestamp": time.time(),
        }

        # Start collection loop
        asyncio.create_task(self._collection_loop())

    async def stop(self):
        """Stop metrics collection"""
        self.running = False

    async def _collection_loop(self):
        """Main collection loop"""
        while self.running:
            await self._collect_system_metrics()
            await asyncio.sleep(self.collection_interval)

    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        current_time = time.time()

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.system_metrics.cpu_percent.append(
            MetricPoint(timestamp=current_time, value=cpu_percent)
        )

        # Memory usage
        memory = psutil.virtual_memory()
        self.system_metrics.memory_percent.append(
            MetricPoint(timestamp=current_time, value=memory.percent)
        )

        # Network usage (delta from baseline)
        net_io = psutil.net_io_counters()
        if self.network_baseline:
            time_delta = current_time - self.network_baseline["timestamp"]
            if time_delta > 0:
                bytes_sent_delta = (
                    net_io.bytes_sent - self.network_baseline["bytes_sent"]
                )
                bytes_recv_delta = (
                    net_io.bytes_recv - self.network_baseline["bytes_recv"]
                )

                # Calculate rate (bytes per second)
                sent_rate = bytes_sent_delta / time_delta
                recv_rate = bytes_recv_delta / time_delta

                self.system_metrics.network_sent.append(
                    MetricPoint(timestamp=current_time, value=sent_rate)
                )
                self.system_metrics.network_received.append(
                    MetricPoint(timestamp=current_time, value=recv_rate)
                )

            # Update baseline
            self.network_baseline = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "timestamp": current_time,
            }

    def add_peer(self, peer_id: str, peer_name: str):
        """Add a peer to track"""
        if peer_id not in self.peer_metrics:
            self.peer_metrics[peer_id] = PeerMetrics(
                peer_id=peer_id, peer_name=peer_name
            )

    def remove_peer(self, peer_id: str):
        """Remove a peer from tracking"""
        if peer_id in self.peer_metrics:
            self.peer_metrics[peer_id].status = "disconnected"

    async def record_latency(self, peer_id: str, latency: float | None):
        """Record latency measurement for a peer and update quality prediction"""
        if peer_id not in self.peer_metrics:
            return

        current_time = time.time()
        peer = self.peer_metrics[peer_id]

        if latency is not None:
            peer.latency.append(MetricPoint(timestamp=current_time, value=latency))
            peer.last_seen = current_time

            # Calculate jitter (standard deviation of recent latencies)
            if len(peer.latency) >= 2:
                latencies = [p.value for p in peer.latency]
                avg_latency = sum(latencies) / len(latencies)
                variance = sum((x - avg_latency) ** 2 for x in latencies) / len(
                    latencies
                )
                peer.jitter_ms = variance**0.5

            # Update connection quality prediction
            quality_score, quality_status = predict_connection_quality(
                latency_ms=latency,
                packet_loss_percent=peer.packet_loss_percent,
                jitter_ms=peer.jitter_ms,
            )

            # Track quality trend
            prev_score = peer.quality_score
            peer.quality_score = quality_score

            if quality_score > prev_score + 5:
                peer.quality_trend = "improving"
            elif quality_score < prev_score - 5:
                peer.quality_trend = "degrading"
            else:
                peer.quality_trend = "stable"

            # Update status based on quality score
            if quality_score >= 60:
                peer.status = "connected"
            else:
                peer.status = "degraded"
        else:
            # No latency = connection issue
            peer.status = "degraded"
            peer.quality_score = 0.0
            peer.quality_trend = "degrading"

    async def record_bandwidth(
        self, peer_id: str, bytes_sent: int = 0, bytes_received: int = 0
    ):
        """Record bandwidth usage for a peer"""
        if peer_id not in self.peer_metrics:
            return

        peer = self.peer_metrics[peer_id]
        peer.bytes_sent += bytes_sent
        peer.bytes_received += bytes_received

    async def record_packet_loss(self, peer_id: str, packet_loss: float):
        """Record packet loss for a peer"""
        if peer_id not in self.peer_metrics:
            return

        # Store packet loss data (could be added to PeerMetrics if needed)
        peer = self.peer_metrics[peer_id]
        peer.last_seen = time.time()

    async def start_game_session(self, game_id: str, game_name: str, peers: list[str]):
        """Start tracking a game session"""
        self.active_session = GameSession(
            game_id=game_id,
            game_name=game_name,
            started_at=time.time(),
            peers=peers.copy(),
        )

    async def end_game_session(self):
        """End the current game session"""
        if self.active_session:
            self.active_session.ended_at = time.time()
            self.active_session.duration = (
                self.active_session.ended_at - self.active_session.started_at
            )

            # Calculate latency statistics
            latencies = []
            for peer_id in self.active_session.peers:
                if peer_id in self.peer_metrics:
                    peer = self.peer_metrics[peer_id]
                    latencies.extend([p.value for p in peer.latency])

            if latencies:
                self.active_session.avg_latency = sum(latencies) / len(latencies)
                self.active_session.max_latency = max(latencies)
                self.active_session.min_latency = min(latencies)

            # Store session
            self.game_sessions.append(self.active_session)
            self.active_session = None

    async def get_peer_summary(self, peer_id: str) -> dict | None:
        """Get summary statistics for a peer"""
        if peer_id not in self.peer_metrics:
            return None

        peer = self.peer_metrics[peer_id]

        # Calculate latency statistics
        latencies = [p.value for p in peer.latency]
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        min_latency = min(latencies) if latencies else None
        max_latency = max(latencies) if latencies else None
        current_latency = latencies[-1] if latencies else None

        return {
            "peer_id": peer.peer_id,
            "peer_name": peer.peer_name,
            "status": peer.status,
            "latency": {
                "current": current_latency,
                "average": avg_latency,
                "min": min_latency,
                "max": max_latency,
            },
            "bandwidth": {
                "sent": peer.bytes_sent,
                "received": peer.bytes_received,
            },
            "packets": {
                "sent": peer.packets_sent,
                "received": peer.packets_received,
            },
            "uptime": time.time() - peer.last_seen,
            "last_seen": peer.last_seen,
        }

    async def get_all_peers_summary(self) -> list[dict]:
        """Get summary for all peers"""
        summaries = []
        for peer_id in self.peer_metrics:
            summary = await self.get_peer_summary(peer_id)
            if summary:
                summaries.append(summary)
        return summaries

    def get_system_summary(self) -> dict:
        """Get system metrics summary"""
        cpu_values = [p.value for p in self.system_metrics.cpu_percent]
        memory_values = [p.value for p in self.system_metrics.memory_percent]
        sent_values = [p.value for p in self.system_metrics.network_sent]
        recv_values = [p.value for p in self.system_metrics.network_received]

        return {
            "cpu": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
            },
            "memory": {
                "current": memory_values[-1] if memory_values else 0,
                "average": (
                    sum(memory_values) / len(memory_values) if memory_values else 0
                ),
                "max": max(memory_values) if memory_values else 0,
            },
            "network": {
                "sent_rate": sent_values[-1] if sent_values else 0,
                "recv_rate": recv_values[-1] if recv_values else 0,
                "total_sent": (
                    sum(sent_values) * self.collection_interval if sent_values else 0
                ),
                "total_recv": (
                    sum(recv_values) * self.collection_interval if recv_values else 0
                ),
            },
        }

    def get_latency_history(self, peer_id: str, duration: int = 3600) -> list[dict]:
        """Get latency history for a peer

        Args:
            peer_id: Peer ID
            duration: Duration in seconds (default 1 hour)
        """
        if peer_id not in self.peer_metrics:
            return []

        peer = self.peer_metrics[peer_id]
        current_time = time.time()
        cutoff_time = current_time - duration

        return [
            {"timestamp": p.timestamp, "value": p.value}
            for p in peer.latency
            if p.timestamp >= cutoff_time
        ]

    def get_system_history(self, duration: int = 3600) -> dict:
        """Get system metrics history

        Args:
            duration: Duration in seconds (default 1 hour)
        """
        current_time = time.time()
        cutoff_time = current_time - duration

        def filter_points(points):
            return [
                {"timestamp": p.timestamp, "value": p.value}
                for p in points
                if p.timestamp >= cutoff_time
            ]

        return {
            "cpu": filter_points(self.system_metrics.cpu_percent),
            "memory": filter_points(self.system_metrics.memory_percent),
            "network_sent": filter_points(self.system_metrics.network_sent),
            "network_received": filter_points(self.system_metrics.network_received),
        }

    def get_game_sessions(self, limit: int = 10) -> list[dict]:
        """Get recent game sessions"""
        sessions = list(self.game_sessions)[-limit:]

        return [
            {
                "game_id": s.game_id,
                "game_name": s.game_name,
                "started_at": s.started_at,
                "ended_at": s.ended_at,
                "duration": s.duration,
                "peers": s.peers,
                "latency": {
                    "average": s.avg_latency,
                    "min": s.min_latency,
                    "max": s.max_latency,
                },
            }
            for s in sessions
        ]

    def get_network_quality_score(self) -> float:
        """Calculate overall network quality score (0-100)"""
        scores = []

        # Peer latency score
        for peer_id in self.peer_metrics:
            peer = self.peer_metrics[peer_id]
            if peer.latency:
                avg_latency = sum(p.value for p in peer.latency) / len(peer.latency)
                # Score: 100 at 0ms, 0 at 500ms
                latency_score = max(0, 100 - (avg_latency / 5))
                scores.append(latency_score)

        # System performance score
        cpu_values = [p.value for p in self.system_metrics.cpu_percent]
        if cpu_values:
            avg_cpu = sum(cpu_values) / len(cpu_values)
            # Score: 100 at 0%, 0 at 100%
            cpu_score = max(0, 100 - avg_cpu)
            scores.append(cpu_score)

        return sum(scores) / len(scores) if scores else 100.0

    def get_peer_connection_quality(self, peer_id: str) -> dict | None:
        """Get detailed connection quality metrics for a peer

        Returns:
            Dictionary with quality metrics or None if peer not found
        """
        if peer_id not in self.peer_metrics:
            return None

        peer = self.peer_metrics[peer_id]

        # Calculate average latency
        avg_latency = None
        if peer.latency:
            avg_latency = sum(p.value for p in peer.latency) / len(peer.latency)

        return {
            "peer_id": peer_id,
            "peer_name": peer.peer_name,
            "quality_score": peer.quality_score,
            "quality_status": (
                "excellent"
                if peer.quality_score >= 80
                else (
                    "good"
                    if peer.quality_score >= 60
                    else "fair" if peer.quality_score >= 40 else "poor"
                )
            ),
            "quality_trend": peer.quality_trend,
            "status": peer.status,
            "avg_latency_ms": avg_latency,
            "jitter_ms": peer.jitter_ms,
            "packet_loss_percent": peer.packet_loss_percent,
            "bytes_sent": peer.bytes_sent,
            "bytes_received": peer.bytes_received,
            "uptime_seconds": peer.connection_uptime,
        }

    def get_aggregated_system_metrics(self, window_seconds: float = 60.0) -> dict:
        """Get aggregated system metrics for a time window

        Useful for trending analysis and long-term monitoring.

        Args:
            window_seconds: Time window in seconds

        Returns:
            Dictionary with aggregated CPU, memory, and network stats
        """
        current_time = time.time()

        return {
            "cpu": aggregate_metrics_by_window(
                list(self.system_metrics.cpu_percent), window_seconds, current_time
            ),
            "memory": aggregate_metrics_by_window(
                list(self.system_metrics.memory_percent), window_seconds, current_time
            ),
            "network_sent": aggregate_metrics_by_window(
                list(self.system_metrics.network_sent), window_seconds, current_time
            ),
            "network_received": aggregate_metrics_by_window(
                list(self.system_metrics.network_received), window_seconds, current_time
            ),
            "window_seconds": window_seconds,
            "timestamp": current_time,
        }

    def get_aggregated_peer_metrics(
        self, peer_id: str, window_seconds: float = 60.0
    ) -> dict | None:
        """Get aggregated metrics for a specific peer

        Args:
            peer_id: Peer ID to get metrics for
            window_seconds: Time window in seconds

        Returns:
            Dictionary with aggregated latency stats or None if peer not found
        """
        if peer_id not in self.peer_metrics:
            return None

        peer = self.peer_metrics[peer_id]
        current_time = time.time()

        return {
            "peer_id": peer_id,
            "peer_name": peer.peer_name,
            "latency": aggregate_metrics_by_window(
                list(peer.latency), window_seconds, current_time
            ),
            "quality_score": peer.quality_score,
            "quality_trend": peer.quality_trend,
            "status": peer.status,
            "window_seconds": window_seconds,
            "timestamp": current_time,
        }
