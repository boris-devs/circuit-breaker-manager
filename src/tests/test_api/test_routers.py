import json

import pytest
from fastapi.testclient import TestClient


@pytest.mark.anyio
async def test_create_service(client):
    data = {"name": "test service", "url": "http://test.com", "state": "OPEN"}
    response = await client.post("/register_service/", json=data)
    assert response.status_code == 201
    assert response.json()["name"] == "test service"


@pytest.mark.anyio
async def test_create_service_invalid_data(client):
    invalid_data = {"name": "bad service", "url": "not-a-url", "state": "OPEN"}
    response = await client.post("/register_service/", json=invalid_data)

    assert response.status_code == 422


@pytest.mark.anyio
async def test_health_service_caching_logic(client, _redis_client):
    data = {"name": "cache service", "url": "https://cache.com", "state": "CLOSED"}
    create_res = await client.post("/register_service/", json=data)
    service_id = create_res.json()["id"]

    await client.get(f"/health/{service_id}/")

    fake_status = create_res.json()
    fake_status["state"] = "OPEN"
    await _redis_client.set(f"service_status:{service_id}", json.dumps(fake_status))

    response = await client.get(f"/health/{service_id}/")
    assert response.json()["state"] == "OPEN"


@pytest.mark.anyio
async def test_service_not_found(client):
    response = await client.get("/services/99999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_health_service(client, _redis_client):
    data = {"name": "health service", "url": "https://test.com", "state": "OPEN"}
    keys_redis = await _redis_client.keys("*")
    assert len(keys_redis) == 0
    await client.post("/register_service/", json=data)
    response = await client.get("/health/1/")
    assert response.status_code == 200
    cached_data = await _redis_client.get("service_status:1")
    assert json.loads(cached_data) == response.json()


@pytest.mark.anyio
async def test_trip_circuit_breaker(client, _redis_client):
    data = {"name": "test trip service", "url": "https://google.com", "state": "CLOSED"}

    create_service_response = await client.post("/register_service/", json=data)
    id_created_service = create_service_response.json()["id"]
    assert create_service_response.status_code == 201
    assert create_service_response.json()["state"] == "CLOSED"

    trip_response = await client.post(f"/circuit-breaker/{id_created_service}/trip/")
    assert trip_response.status_code == 200
    assert trip_response.json()["state"] == "OPEN"
    assert trip_response.json()["id"] == id_created_service

    cached_data = await _redis_client.get(f"service_status:{id_created_service}")
    assert json.loads(cached_data) == trip_response.json()


@pytest.mark.anyio
async def test_trip_circuit_breaker_not_found(client):
    response = await client.post("/circuit-breaker/99999/trip/")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_websocket_endpoint(_app):
    with TestClient(_app) as ws_client:
        with ws_client.websocket_connect("api/v1/ws/status") as websocket:
            data = websocket.receive_text()
            assert data == "Connected to websocket!"
