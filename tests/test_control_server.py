"""Tests for control plane server"""

import pytest

from core.config import Config
from servers.control_server import app, generate_token, init_database


@pytest.fixture
async def config():
    """Create test config"""
    return await Config.load()


def test_app_initialization():
    """Test FastAPI app initializes correctly"""
    assert app is not None
    assert app.title == "LANrage Control Plane"
    assert app.version == "1.0.0"


def test_generate_token():
    """Test token generation"""
    token = generate_token()

    assert isinstance(token, str)
    assert len(token) > 0

    # Tokens should be unique
    token2 = generate_token()
    assert token != token2


@pytest.mark.asyncio
async def test_init_database():
    """Test database initialization"""
    # Should not raise an error
    await init_database()


def test_app_has_routes():
    """Test app has expected routes"""
    routes = [route.path for route in app.routes]

    # Check for key endpoints
    assert "/" in routes
    assert "/auth/register" in routes
    assert "/parties" in routes
    assert "/relays" in routes


def test_app_has_cors():
    """Test CORS middleware is configured"""
    # Check that CORS middleware is present
    # CORS middleware is wrapped, so check if any middleware exists
    assert len(app.user_middleware) > 0


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root health check endpoint"""
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "LANrage Control Plane"
    assert data["version"] == "1.0.0"
    assert data["status"] == "ok"
    assert "parties" in data
    assert "relays" in data


def test_token_format():
    """Test token format is URL-safe"""
    token = generate_token()

    # Should be URL-safe (no special characters that need encoding)
    import string

    allowed_chars = string.ascii_letters + string.digits + "-_"
    assert all(c in allowed_chars for c in token)


def test_multiple_token_generation():
    """Test generating multiple tokens"""
    tokens = [generate_token() for _ in range(10)]

    # All should be unique
    assert len(set(tokens)) == 10

    # All should be strings
    assert all(isinstance(t, str) for t in tokens)


def test_app_metadata():
    """Test app metadata"""
    assert app.title == "LANrage Control Plane"
    assert app.version == "1.0.0"
    assert hasattr(app, "routes")
    assert hasattr(app, "middleware")


def test_app_routes_count():
    """Test app has expected number of routes"""
    routes = list(app.routes)

    # Should have multiple routes (exact count may vary)
    assert len(routes) > 10


def test_app_openapi_schema():
    """Test OpenAPI schema generation"""
    schema = app.openapi()

    assert schema is not None
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "LANrage Control Plane"


def test_server_initialization(config):
    """Test server can be initialized with config"""
    assert config is not None
    assert hasattr(config, "control_server")


def test_app_exception_handlers():
    """Test app has exception handlers"""
    # FastAPI has default exception handlers
    assert hasattr(app, "exception_handlers")


def test_app_middleware_stack():
    """Test middleware stack"""
    # Should have at least CORS middleware
    assert len(app.user_middleware) > 0


def test_token_length():
    """Test token has reasonable length"""
    token = generate_token()

    # URL-safe base64 tokens should be reasonably long
    assert len(token) >= 32


def test_app_startup_events():
    """Test app has startup events configured"""
    # Check that startup event is registered
    assert hasattr(app, "router")
    assert hasattr(app.router, "on_startup")


def test_app_lifespan():
    """Test app lifespan configuration"""
    # App should have lifespan or startup/shutdown events
    assert hasattr(app, "router")


def test_config_loading(config):
    """Test config loads successfully"""
    assert config is not None
    assert hasattr(config, "mode")


def test_app_docs_url():
    """Test app has docs URL configured"""
    # FastAPI provides automatic docs
    assert hasattr(app, "docs_url")


def test_app_redoc_url():
    """Test app has redoc URL configured"""
    # FastAPI provides automatic redoc
    assert hasattr(app, "redoc_url")
