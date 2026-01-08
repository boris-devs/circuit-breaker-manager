import json
from datetime import datetime, timezone, timedelta

import pytest
from unittest.mock import patch, AsyncMock

from sqlalchemy import update
from starlette.testclient import TestClient

from database.models.circuit_breaker import MonitoredServices


@pytest.mark.anyio
async def test_circuit_breaker_full_cycle_e2e(client, db_session, _redis_client):
    """
    E2E scenario for Circuit Breaker lifecycle:
    1. Register a service via API.
    2. Simulate that the check interval has passed.
    3. Trigger background monitoring and handle a failure.
    4. Verify failure count increment.
    5. Manually trip the circuit breaker to OPEN state.
    """
    service_data = {"name": "external-api", "url": "http://failing.com", "state": "CLOSED"}
    register_resp = await client.post("/register_service/", json=service_data)
    assert register_resp.status_code == 201
    service_id = register_resp.json()["id"]

    past_time = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.execute(
        update(MonitoredServices)
        .where(MonitoredServices.id == service_id)
        .values(last_check=past_time)
    )
    await db_session.commit()

    def get_test_session_factory():
        return lambda: db_session

    with patch("tasks.tasks.get_session_factory", side_effect=get_test_session_factory), \
            patch("tasks.tasks.get_redis_client", return_value=_redis_client), \
            patch("tasks.monitoring.check_health_service", new_callable=AsyncMock, return_value=False), \
            patch("tasks.tasks.queue.enqueue") as mock_enqueue:
        from tasks.tasks import run_monitoring_and_notify_job, check_service_availability_task

        await run_monitoring_and_notify_job()
        assert mock_enqueue.called, "Monitoring job didn't find the service"

        args, _ = mock_enqueue.call_args
        await check_service_availability_task(args[1])

    db_session.expire_all()
    health_resp = await client.get(f"/health/{service_id}/")
    assert health_resp.status_code == 200

    last_check_dt = datetime.fromisoformat(health_resp.json()["last_check"])
    if last_check_dt.tzinfo is None:
        last_check_dt = last_check_dt.replace(tzinfo=timezone.utc)

    assert last_check_dt >= past_time
    assert health_resp.json()["state"] == "CLOSED"
    assert health_resp.json()["failure_count"] == 1

    cached_data = await _redis_client.get(f"service_status:{service_id}")
    assert json.loads(cached_data)["failure_count"] == 1

    # --- ACT (Manual trip) ---
    # Force trip the circuit breaker to OPEN state
    trip_resp = await client.post(f"/circuit-breaker/{service_id}/trip/")

    assert trip_resp.status_code == 200
    assert trip_resp.json()["state"] == "OPEN"

    cached_data_trip = await _redis_client.get(f"service_status:{service_id}")
    assert json.loads(cached_data_trip)["state"] == "OPEN"


@pytest.mark.anyio
async def test_websocket_notification_on_failure(_app, _redis_client):
    from services.websocket_manager import ws_manager
    from services.redis_pubsub_manager import redis_pubsub_manager
    redis_pubsub_manager.redis_client = _redis_client
    with TestClient(app=_app) as ws_client:
        with ws_client.websocket_connect("api/v1/ws/status") as websocket:
            _ = websocket.receive_text()

            await redis_pubsub_manager.publish()

            await ws_manager.broadcast(f"Service 1 changed to OPEN")

            message = websocket.receive_text()
            assert "OPEN" in message
