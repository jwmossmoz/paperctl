"""Tests for SWOClient."""

import pytest
from pytest_httpx import HTTPXMock

from paperctl.client import SWOClient
from paperctl.client.exceptions import APIError, AuthenticationError, RateLimitError

BASE_URL = "https://api.na-01.cloud.solarwinds.com"


@pytest.fixture
def client() -> SWOClient:
    return SWOClient("test-token")


def test_get_logs(httpx_mock: HTTPXMock, client: SWOClient) -> None:
    """Test get_logs parses LogsResponse correctly."""
    httpx_mock.add_response(
        url=f"{BASE_URL}/v1/logs?pageSize=1000&direction=backward",
        json={
            "logs": [
                {
                    "time": "2024-01-01T00:00:00Z",
                    "message": "test log",
                    "hostname": "web-1",
                    "severity": "info",
                    "program": "nginx",
                }
            ],
            "pageInfo": {"prevPage": "", "nextPage": ""},
        },
    )

    response = client.get_logs()
    assert len(response.logs) == 1
    assert response.logs[0].message == "test log"
    assert response.logs[0].hostname == "web-1"
    assert response.page_info.next_page == ""


def test_get_logs_with_hostname(httpx_mock: HTTPXMock, client: SWOClient) -> None:
    """Test get_logs prepends host filter."""
    httpx_mock.add_response(
        json={"logs": [], "pageInfo": {"prevPage": "", "nextPage": ""}},
    )

    response = client.get_logs(hostname="web-1")
    assert len(response.logs) == 0

    request = httpx_mock.get_request()
    assert request is not None
    assert request.url.params["filter"] == 'host:"web-1"'


def test_logs_iter_pagination(httpx_mock: HTTPXMock, client: SWOClient) -> None:
    """Test logs_iter paginates via nextPage URLs."""
    next_url = f"{BASE_URL}/v1/logs?cursor=abc123"

    # First page with nextPage
    httpx_mock.add_response(
        url=f"{BASE_URL}/v1/logs?pageSize=1000&direction=backward",
        json={
            "logs": [
                {
                    "time": "2024-01-01T00:00:00Z",
                    "message": "event 1",
                    "hostname": "web-1",
                }
            ],
            "pageInfo": {"prevPage": "", "nextPage": next_url},
        },
    )

    # Second page (empty nextPage = stop)
    httpx_mock.add_response(
        url=next_url,
        json={
            "logs": [
                {
                    "time": "2024-01-01T00:01:00Z",
                    "message": "event 2",
                    "hostname": "web-1",
                }
            ],
            "pageInfo": {"prevPage": "", "nextPage": ""},
        },
    )

    events = list(client.logs_iter())
    assert len(events) == 2
    assert events[0].message == "event 1"
    assert events[1].message == "event 2"


def test_logs_iter_total_limit(httpx_mock: HTTPXMock, client: SWOClient) -> None:
    """Test logs_iter respects total_limit."""
    httpx_mock.add_response(
        json={
            "logs": [
                {"time": "2024-01-01T00:00:00Z", "message": f"event {i}", "hostname": "web-1"}
                for i in range(5)
            ],
            "pageInfo": {"prevPage": "", "nextPage": ""},
        },
    )

    events = list(client.logs_iter(total_limit=3))
    assert len(events) == 3


def test_list_entities(httpx_mock: HTTPXMock, client: SWOClient) -> None:
    """Test list_entities parses entities."""
    httpx_mock.add_response(
        url=f"{BASE_URL}/v1/entities?type=Host&pageSize=100",
        json={
            "entities": [
                {
                    "id": "e-1",
                    "type": "Host",
                    "name": "web-1",
                    "displayName": "Web Server 1",
                    "inMaintenance": False,
                    "tags": {},
                    "attributes": {},
                }
            ],
            "pageInfo": {"prevPage": "", "nextPage": ""},
        },
    )

    entities = client.list_entities()
    assert len(entities) == 1
    assert entities[0].name == "web-1"
    assert entities[0].id == "e-1"


def test_get_entity(httpx_mock: HTTPXMock, client: SWOClient) -> None:
    """Test get_entity parses single entity."""
    httpx_mock.add_response(
        url=f"{BASE_URL}/v1/entities/e-1",
        json={
            "id": "e-1",
            "type": "Host",
            "name": "web-1",
            "displayName": "Web Server 1",
            "inMaintenance": False,
            "tags": {},
            "attributes": {},
        },
    )

    entity = client.get_entity("e-1")
    assert entity.name == "web-1"
    assert entity.type == "Host"


def test_list_entity_types(httpx_mock: HTTPXMock, client: SWOClient) -> None:
    """Test list_entity_types returns type strings."""
    httpx_mock.add_response(
        url=f"{BASE_URL}/v1/metadata/entities/types",
        json={"types": ["Host", "Service", "Network"]},
    )

    types = client.list_entity_types()
    assert types == ["Host", "Service", "Network"]


def test_authentication_error(httpx_mock: HTTPXMock, client: SWOClient) -> None:
    """Test 401 raises AuthenticationError."""
    httpx_mock.add_response(status_code=401)

    with pytest.raises(AuthenticationError):
        client.get_logs()


def test_rate_limit_error(httpx_mock: HTTPXMock, client: SWOClient) -> None:
    """Test 429 raises RateLimitError."""
    httpx_mock.add_response(
        status_code=429,
        headers={"Retry-After": "5"},
    )

    with pytest.raises(RateLimitError) as exc_info:
        client.get_logs()
    assert exc_info.value.retry_after == 5


def test_server_error(httpx_mock: HTTPXMock, client: SWOClient) -> None:
    """Test 500 raises APIError."""
    httpx_mock.add_response(
        status_code=500,
        json={"message": "Internal server error"},
    )

    with pytest.raises(APIError) as exc_info:
        client.get_logs()
    assert exc_info.value.status_code == 500
