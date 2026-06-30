"""Pytest configuration."""
import pytest


@pytest.fixture
def sample_env():
    """Sample environment variables for tests."""
    return {
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "REDIS_URL": "redis://localhost:6379/0",
        "ELASTICSEARCH_URL": "http://localhost:9200",
    }