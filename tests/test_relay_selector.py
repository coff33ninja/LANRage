"""Tests for intelligent relay selection."""

import time

from core.relay_selector import RelayCandidate, RelaySelector


def test_direct_connection_preferred_when_quality_high():
    selector = RelaySelector(direct_threshold=80.0)
    result = selector.select_relay(
        peer_a="p1",
        peer_b="p2",
        peer_a_direct_quality=95.0,
        peer_b_direct_quality=90.0,
        candidates=[],
    )
    assert result.mode == "direct"
    assert result.selected_relay is None


def test_select_best_relay_from_candidates():
    selector = RelaySelector(direct_threshold=90.0)
    result = selector.select_relay(
        peer_a="p1",
        peer_b="p2",
        peer_a_direct_quality=45.0,
        peer_b_direct_quality=50.0,
        candidates=[
            RelayCandidate(
                relay_id="relay-a",
                health_score=90.0,
                load_percent=30.0,
                peer_quality={"p1": 70.0, "p2": 80.0},
            ),
            RelayCandidate(
                relay_id="relay-b",
                health_score=98.0,
                load_percent=10.0,
                peer_quality={"p1": 85.0, "p2": 88.0},
            ),
        ],
    )
    assert result.mode == "relay"
    assert result.selected_relay == "relay-b"


def test_relay_failover_excludes_recently_failed_primary():
    selector = RelaySelector(direct_threshold=90.0, failover_cooldown_s=2.0)
    selector.mark_relay_failed("relay-primary", failed_at=time.time())
    result = selector.select_relay(
        peer_a="p1",
        peer_b="p2",
        peer_a_direct_quality=20.0,
        peer_b_direct_quality=20.0,
        candidates=[
            RelayCandidate(
                relay_id="relay-primary",
                health_score=100.0,
                load_percent=0.0,
                peer_quality={"p1": 95.0, "p2": 95.0},
            ),
            RelayCandidate(
                relay_id="relay-secondary",
                health_score=85.0,
                load_percent=10.0,
                peer_quality={"p1": 80.0, "p2": 80.0},
            ),
        ],
    )
    assert result.selected_relay == "relay-secondary"


def test_preferred_region_boosts_geographic_fallback():
    selector = RelaySelector(direct_threshold=90.0)
    result = selector.select_relay(
        peer_a="p1",
        peer_b="p2",
        peer_a_direct_quality=10.0,
        peer_b_direct_quality=10.0,
        preferred_region="us-east",
        candidates=[
            RelayCandidate(
                relay_id="relay-eu",
                region="eu-west",
                health_score=95.0,
                load_percent=15.0,
                peer_quality={"p1": 80.0, "p2": 82.0},
            ),
            RelayCandidate(
                relay_id="relay-us",
                region="us-east",
                health_score=92.0,
                load_percent=15.0,
                peer_quality={"p1": 79.0, "p2": 81.0},
            ),
        ],
    )
    assert result.selected_relay == "relay-us"


def test_fallback_relays_returned_in_priority_order():
    selector = RelaySelector(direct_threshold=95.0)
    result = selector.select_relay(
        peer_a="p1",
        peer_b="p2",
        peer_a_direct_quality=20.0,
        peer_b_direct_quality=20.0,
        candidates=[
            RelayCandidate(
                relay_id="relay-1",
                health_score=98.0,
                load_percent=5.0,
                peer_quality={"p1": 90.0, "p2": 90.0},
            ),
            RelayCandidate(
                relay_id="relay-2",
                health_score=85.0,
                load_percent=10.0,
                peer_quality={"p1": 80.0, "p2": 80.0},
            ),
            RelayCandidate(
                relay_id="relay-3",
                health_score=70.0,
                load_percent=20.0,
                peer_quality={"p1": 70.0, "p2": 70.0},
            ),
        ],
    )
    assert result.selected_relay == "relay-1"
    assert result.fallback_relays == ["relay-2", "relay-3"]
