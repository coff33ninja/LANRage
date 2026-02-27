"""Auth enforcement tests for control-plane server routes."""

from fastapi.testclient import TestClient

from servers.control_server import app


def test_relays_requires_auth_token():
    """Relay listing should reject unauthenticated requests."""
    client = TestClient(app)
    response = client.get("/relays")
    assert response.status_code == 401


def test_relays_accepts_valid_token():
    """Relay listing should succeed with a valid Bearer token."""
    client = TestClient(app)

    token_response = client.post("/auth/register", params={"peer_id": "test-peer-auth"})
    assert token_response.status_code == 200
    token = token_response.json()["token"]

    response = client.get("/relays", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "relays" in response.json()
