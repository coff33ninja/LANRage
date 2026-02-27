"""Tests for Prometheus /metrics endpoint."""

from fastapi.testclient import TestClient

from api.server import app
import api.server as server_module


class _DummyMetrics:
    async def get_all_peers_summary(self):
        return [{"peer_id": "p1"}, {"peer_id": "p2"}]

    def get_system_summary(self):
        return {"avg_latency_ms": 12.5, "avg_packet_loss": 0.4}

    def get_network_quality_score(self):
        return {"score": 97.0}


def test_prometheus_metrics_endpoint_exposes_expected_metrics():
    """`/metrics` should return Prometheus-formatted output."""
    old_metrics = server_module.metrics_collector
    server_module.metrics_collector = _DummyMetrics()
    try:
        client = TestClient(app)
        response = client.get("/metrics")
        assert response.status_code == 200
        body = response.text
        assert "lanrage_peers_total 2" in body
        assert "lanrage_latency_avg_ms 12.5" in body
        assert "lanrage_packet_loss_percent 0.4" in body
        assert "lanrage_quality_score 97.0" in body
    finally:
        server_module.metrics_collector = old_metrics
