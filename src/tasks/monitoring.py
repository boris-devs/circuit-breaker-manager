from datetime import timezone, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.circuit_breaker import MonitoredServices, StateServiceEnum
from services.life_checker import check_health_service


async def check_service_availability(service: MonitoredServices, db: AsyncSession):
    now = datetime.now(timezone.utc)

    service.last_check = now
    if service.state == StateServiceEnum.OPEN:
        if service.last_failure_time:
            unlock_time = service.last_failure_time + timedelta(service.recovery_timeout)
            if now < unlock_time:
                service.state = StateServiceEnum.HALF_OPEN
                await db.commit()
                return


    is_healthy = await check_health_service(service.url)
    if is_healthy:
        await service_available_success(service)
    else:
        await service_available_failure(service)
    await db.commit()


async def service_available_failure(service: MonitoredServices):
    service.failure_count += 1
    service.last_failure_time = datetime.now(timezone.utc)
    if service.failure_count < service.failure_threshold:
        service.state = StateServiceEnum.OPEN
        service.last_failure_time = datetime.now(timezone.utc)
        service.last_check = datetime.now(timezone.utc)


async def service_available_success(service: MonitoredServices):
    service.state = StateServiceEnum.CLOSED
    service.last_check = datetime.now(timezone.utc)
    service.failure_count = 0
