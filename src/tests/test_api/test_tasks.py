import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
from database.models.circuit_breaker import MonitoredServices, StateServiceEnum
from tasks.monitoring import check_service_availability
from services.service_status_cache import RedisServiceStatusCache

@pytest.mark.anyio
async def test_check_service_availability_to_open(db_session, _redis_client):
    cache = RedisServiceStatusCache(_redis_client)

    service = MonitoredServices(
        id=1,
        name="fail service",
        url="http://failure.com",
        state=StateServiceEnum.CLOSED,
        failure_threshold=1,
        failure_count=0,
        recovery_timeout=30
    )

    with patch("tasks.monitoring.check_health_service", return_value=False), \
            patch("tasks.monitoring.service_create_logs", new_callable=AsyncMock):
        await check_service_availability(service, db_session, cache)

        assert service.state == StateServiceEnum.OPEN
        assert service.failure_count == 1


@pytest.mark.anyio
async def test_half_open_to_closed_success(db_session, _redis_client):
    cache = RedisServiceStatusCache(_redis_client)

    last_failure = datetime.now(timezone.utc) - timedelta(seconds=60)
    service = MonitoredServices(
        id=2,
        name="success service",
        url="http://success.com",
        state=StateServiceEnum.OPEN,
        last_failure_time=last_failure,
        recovery_timeout=30,
        failure_count=5
    )

    with patch("tasks.monitoring.check_health_service", return_value=True), \
            patch("tasks.monitoring.service_create_logs", new_callable=AsyncMock):
        await check_service_availability(service, db_session, cache)

        assert service.state == StateServiceEnum.CLOSED
        assert service.failure_count == 0