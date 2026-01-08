import json

import pytest
import httpx

from services.redis_pubsub_manager import RedisPubSubManager
from src.services.life_checker import check_health_service

@pytest.mark.anyio
async def test_check_health_service_success(respx_mock):
    respx_mock.get("https://example.com").return_value = httpx.Response(200)
    result = await check_health_service("example.com")
    assert result is True

@pytest.mark.anyio
async def test_check_health_service_404(respx_mock):
    respx_mock.get("https://test.com").return_value = httpx.Response(404)
    result = await check_health_service("https://test.com")
    assert result is False

@pytest.mark.anyio
async def test_check_health_service_timeout(respx_mock):
    respx_mock.get("https://timeout.com").side_effect = httpx.TimeoutException("Timeout")
    result = await check_health_service("https://timeout.com")
    assert result is False

@pytest.mark.anyio
async def test_check_health_service_connect_error(respx_mock):
    respx_mock.get("https://error.com").side_effect = httpx.ConnectError("Conn error")
    result = await check_health_service("https://error.com")
    assert result is False


@pytest.mark.anyio
async def test_get_cached_statuses_empty(_redis_client):
    manager = RedisPubSubManager(redis_client=_redis_client)
    statuses = await manager.get_cached_statuses()
    assert statuses == []


@pytest.mark.anyio
async def test_get_cached_statuses_with_data(_redis_client):
    manager = RedisPubSubManager(redis_client=_redis_client)
    test_data = {"id": 1, "status": "CLOSED"}
    await _redis_client.set("service_status:1", json.dumps(test_data))

    statuses = await manager.get_cached_statuses()
    assert len(statuses) == 1
    assert statuses[0]["id"] == 1


@pytest.mark.anyio
async def test_publish_without_client():
    manager = RedisPubSubManager(redis_client=None)
    with pytest.raises(RuntimeError, match="Redis client is not set"):
        await manager.publish()