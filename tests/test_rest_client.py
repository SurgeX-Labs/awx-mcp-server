"""Unit tests for RestAWXClient request handling (mocked; no live AWX).

Covers the correctness fixes:
- DELETE goes through _request, so a failed delete raises instead of
  silently "succeeding".
- 204 / empty bodies return cleanly (no JSON decode error).
- Mutating methods (POST) are NOT retried; idempotent GETs are.
"""

import json
import uuid

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock

from awx_mcp_server.clients.rest_client import RestAWXClient
from awx_mcp_server.domain import (
    AWXClientError,
    AWXConnectionError,
    EnvironmentConfig,
)


def _client():
    cfg = EnvironmentConfig(
        env_id=str(uuid.uuid4()),
        name="test",
        base_url="https://awx.example/",
        verify_ssl=True,
    )
    return RestAWXClient(cfg, "user", "pass", is_token=False)


def _response(status_code, content=b"{}"):
    r = MagicMock()
    r.status_code = status_code
    r.content = content
    r.text = content.decode() if content else ""
    r.json = lambda: json.loads(content or b"{}")
    return r


async def test_failed_delete_raises():
    """A DELETE returning 4xx must raise, not silently succeed."""
    client = _client()
    client.client.request = AsyncMock(return_value=_response(403))
    with pytest.raises(AWXClientError):  # AWXAuthenticationError is a subclass
        await client.delete_credential(5)


async def test_delete_204_returns_cleanly():
    """A 204 No Content DELETE must not raise a JSON decode error."""
    client = _client()
    client.client.request = AsyncMock(return_value=_response(204, b""))
    # Should complete without raising.
    await client.delete_credential(5)


async def test_post_is_not_retried():
    """Mutating POSTs must not be retried (avoid duplicate launches)."""
    client = _client()
    attempts = {"n": 0}

    async def boom(method, endpoint, **kwargs):
        attempts["n"] += 1
        raise httpx.ConnectError("connection refused")

    client.client.request = boom
    with pytest.raises(AWXConnectionError):
        await client.launch_job(1)
    assert attempts["n"] == 1, "POST should be attempted exactly once"


async def test_get_is_retried():
    """Idempotent GETs are retried on transient connection errors (3 attempts)."""
    client = _client()
    attempts = {"n": 0}

    async def boom(method, endpoint, **kwargs):
        attempts["n"] += 1
        raise httpx.ConnectError("connection refused")

    client.client.request = boom
    # test_connection swallows the final error and returns False.
    result = await client.test_connection()
    assert result is False
    assert attempts["n"] == 3, "GET should be retried up to 3 attempts"
