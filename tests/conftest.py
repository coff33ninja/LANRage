"""
Pytest configuration and shared fixtures for LANrage tests

This module provides test fixtures and setup/teardown logic for all tests.
Most importantly, it initializes the settings database before tests run.
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session", autouse=True)
async def initialize_test_database():
    """
    Initialize the settings database with default values before any tests run.

    This fixture runs once per test session and is automatically used by all tests.
    It ensures that Config.load() will work in tests by populating the database.
    """
    from core.settings import get_settings_db, init_default_settings

    # Initialize database with defaults
    db = await get_settings_db()
    await init_default_settings()

    # Validate database is ready
    settings = await db.get_all_settings()
    assert settings, "Database initialization failed - no settings found"

    # Yield to run tests
    yield

    # Cleanup after all tests (optional)
    # Could delete test database here if needed


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the entire test session.

    This ensures async fixtures work properly across all tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
