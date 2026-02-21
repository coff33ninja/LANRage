"""Intelligent relay selection based on peer quality and relay health."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from .logging_config import get_logger, set_context, timing_decorator

logger = get_logger(__name__)


@dataclass
class RelayCandidate:
    """Relay candidate metrics used for selection."""

    relay_id: str
    region: str = "global"
    health_score: float = 100.0
    load_percent: float = 0.0
    peer_quality: dict[str, float] = field(default_factory=dict)


@dataclass
class RelaySelection:
    """Relay selection result."""

    mode: str  # direct | relay
    selected_relay: str | None
    score: float
    reason: str
    fallback_relays: list[str] = field(default_factory=list)


class RelaySelector:
    """Selects the best relay for a peer pair with automatic fallback ordering."""

    def __init__(self, direct_threshold: float = 80.0, failover_cooldown_s: float = 2.0):
        self.direct_threshold = direct_threshold
        self.failover_cooldown_s = failover_cooldown_s
        self.failed_relays: dict[str, float] = {}

    def mark_relay_failed(self, relay_id: str, failed_at: float | None = None) -> None:
        """Mark a relay as failed and temporarily avoid selecting it."""
        self.failed_relays[relay_id] = failed_at if failed_at is not None else time.time()

    def _is_temporarily_failed(self, relay_id: str, now: float) -> bool:
        failed_at = self.failed_relays.get(relay_id)
        if failed_at is None:
            return False
        if now - failed_at >= self.failover_cooldown_s:
            del self.failed_relays[relay_id]
            return False
        return True

    @staticmethod
    def _score_relay(
        peer_a: str,
        peer_b: str,
        candidate: RelayCandidate,
    ) -> float:
        a_quality = max(0.0, min(100.0, candidate.peer_quality.get(peer_a, 0.0)))
        b_quality = max(0.0, min(100.0, candidate.peer_quality.get(peer_b, 0.0)))
        health = max(0.0, min(100.0, candidate.health_score))
        load_factor = 1.0 - (max(0.0, min(100.0, candidate.load_percent)) / 100.0)

        path_quality = math.sqrt(a_quality * b_quality)
        score = ((path_quality * 0.7) + (health * 0.3)) * load_factor
        return max(0.0, min(100.0, score))

    @timing_decorator(name="select_relay")
    def select_relay(
        self,
        peer_a: str,
        peer_b: str,
        peer_a_direct_quality: float,
        peer_b_direct_quality: float,
        candidates: list[RelayCandidate],
        preferred_region: str | None = None,
    ) -> RelaySelection:
        """Select direct path or best relay with fallback ordering."""
        set_context(correlation_id_val=f"{peer_a}:{peer_b}")

        direct_score = math.sqrt(
            max(0.0, min(100.0, peer_a_direct_quality))
            * max(0.0, min(100.0, peer_b_direct_quality))
        )
        if direct_score >= self.direct_threshold:
            return RelaySelection(
                mode="direct",
                selected_relay=None,
                score=direct_score,
                reason="direct_quality_above_threshold",
                fallback_relays=[],
            )

        now = time.time()
        scored_relays: list[tuple[float, RelayCandidate]] = []
        for candidate in candidates:
            if self._is_temporarily_failed(candidate.relay_id, now):
                continue
            score = self._score_relay(peer_a, peer_b, candidate)
            if preferred_region and candidate.region == preferred_region:
                score = min(100.0, score + 5.0)
            scored_relays.append((score, candidate))

        if not scored_relays:
            return RelaySelection(
                mode="direct",
                selected_relay=None,
                score=direct_score,
                reason="no_viable_relay",
                fallback_relays=[],
            )

        scored_relays.sort(key=lambda item: item[0], reverse=True)
        best_score, best_candidate = scored_relays[0]
        fallback_relays = [relay.relay_id for _, relay in scored_relays[1:3]]

        logger.info(
            "Selected relay %s for %s/%s with score %.1f",
            best_candidate.relay_id,
            peer_a,
            peer_b,
            best_score,
        )
        return RelaySelection(
            mode="relay",
            selected_relay=best_candidate.relay_id,
            score=best_score,
            reason="relay_selected_by_score",
            fallback_relays=fallback_relays,
        )
