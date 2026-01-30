"""Pytest configuration and fixtures."""

import pytest

from paperctl.client import PapertrailClient


@pytest.fixture
def api_token() -> str:
    """Mock API token."""
    return "test_token_12345"


@pytest.fixture
def mock_client(api_token: str) -> PapertrailClient:
    """Create a mock Papertrail client."""
    return PapertrailClient(api_token)
