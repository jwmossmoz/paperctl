"""Pytest configuration and fixtures."""

import pytest

from paperctl.client import SWOClient


@pytest.fixture
def api_token() -> str:
    """Mock API token."""
    return "test_token_12345"


@pytest.fixture
def mock_client(api_token: str) -> SWOClient:
    """Create a mock SWO client."""
    return SWOClient(api_token)
