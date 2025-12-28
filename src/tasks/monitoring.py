from datetime import timezone, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.circuit_breaker import MonitoredServices, StateServiceEnum, CircuitBreakerLog
from repository.monitoring_repository import service_create_logs
from services.life_checker import check_health_service


async def check_service_availability(service: MonitoredServices, db: AsyncSession):
    now = datetime.now(timezone.utc)

    service.last_check = now
    if service.state == StateServiceEnum.OPEN:
        if service.last_failure_time:
            unlock_time = service.last_failure_time + timedelta(seconds=service.recovery_timeout)
            if now > unlock_time:
                await service_create_logs(service_id=service.id,
                                          old_state=service.state,
                                          new_state=StateServiceEnum.HALF_OPEN,
                                          db=db)
                service.state = StateServiceEnum.HALF_OPEN
                await db.commit()
                return

    is_healthy = await check_health_service(service.url)
    if is_healthy:
        await service_available_success(service, db)
    else:
        await service_available_failure(service, db)
    await db.commit()


async def service_available_failure(service: MonitoredServices, db: AsyncSession):
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


async def service_available_success(service: MonitoredServices, db: AsyncSession):
    if service.state != StateServiceEnum.CLOSED:
        await service_create_logs(service_id=service.id,
                                  old_state=service.state,
                                  new_state=StateServiceEnum.CLOSED,
                                  db=db)
    service.state = StateServiceEnum.CLOSED
    service.last_check = datetime.now(timezone.utc)
    service.failure_count = 0
