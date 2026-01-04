from datetime import timezone, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.circuit_breaker import MonitoredServices, StateServiceEnum
from repository.monitoring_repository import service_create_logs
from services.service_status_cache import IRedisServiceStatusCache
from services.life_checker import check_health_service


async def check_service_availability(
        service: MonitoredServices,
        db: AsyncSession,
        redis_cache: IRedisServiceStatusCache
):
    now = datetime.now(timezone.utc)

    service.last_check = now
    if service.state == StateServiceEnum.OPEN:
        if service.last_failure_time:
            unlock_time = service.last_failure_time + timedelta(seconds=service.recovery_timeout)
            if now < unlock_time:
                return
            await service_create_logs(service_id=service.id,
                                      old_state=service.state,
                                      new_state=StateServiceEnum.HALF_OPEN,
                                      db=db)
            service.state = StateServiceEnum.HALF_OPEN

            await redis_cache.set_service_status(service_id=service.id,
                                                 service_data=service)

    is_healthy = await check_health_service(service.url)
    if is_healthy:
        await service_available_success(service, db, redis_cache)
    else:
        await service_available_failure(service, db, redis_cache)


async def service_available_failure(
        service: MonitoredServices,
        db: AsyncSession,
        redis_cache: IRedisServiceStatusCache
):
    service.failure_count += 1
    service.last_failure_time = datetime.now(timezone.utc)
    if service.failure_count >= service.failure_threshold:
        await service_create_logs(service_id=service.id,
                                  old_state=service.state,
                                  new_state=StateServiceEnum.OPEN,
                                  db=db)

        service.state = StateServiceEnum.OPEN
        service.last_failure_time = datetime.now(timezone.utc)
        service.last_check = datetime.now(timezone.utc)

        await redis_cache.set_service_status(service_id=service.id,
                                             service_data=service)


async def service_available_success(
        service: MonitoredServices,
        db: AsyncSession,
        redis_cache: IRedisServiceStatusCache
):
    if service.state != StateServiceEnum.CLOSED:
        await service_create_logs(service_id=service.id,
                                  old_state=service.state,
                                  new_state=StateServiceEnum.CLOSED,
                                  db=db)
    service.state = StateServiceEnum.CLOSED
    service.last_check = datetime.now(timezone.utc)
    service.failure_count = 0

    await redis_cache.set_service_status(service_id=service.id,
                                         service_data=service)
