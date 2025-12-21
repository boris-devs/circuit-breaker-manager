from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.circuit_breaker import MonitoredServices, StateServiceEnum
from schemas.monitoring import CreateServiceMonitoringSchema
from utils.life_checker import check_availability


async def create_service_monitoring(service_in: CreateServiceMonitoringSchema, db: AsyncSession):
    new = MonitoredServices(name=service_in.name,
                            url=service_in.url,
                            state=service_in.state,
                            failure_threshold=service_in.failure_threshold,
                            recovery_timeout=service_in.recovery_timeout)
    db.add(new)
    await db.commit()
    await db.refresh(new)
    return new


async def get_service(service_id: int, db: AsyncSession):
    return await db.get(
        MonitoredServices, service_id
    )


async def check_health_service(service: MonitoredServices, db: AsyncSession):
    if service.state == "OPEN":
        time_passed = datetime.now(timezone.utc) - service.last_failure_time
        if time_passed.total_seconds() < service.recovery_timeout:
            return {"status": 503,
                    "recovery_in": service.recovery_timeout - time_passed.total_seconds()}
        else:
            service.state = StateServiceEnum.HALF_OPEN
            await db.commit()
            return {"status": 503}

    is_healthy = await check_availability(service.url)

    if is_healthy:
        service.last_check = datetime.now(timezone.utc)
        if service.state == StateServiceEnum.HALF_OPEN:
            service.state = StateServiceEnum.CLOSED
            service.failure_count = 0
        await db.commit()
        return {"status": 200}
    else:
        service.state = StateServiceEnum.OPEN
        service.last_failure_time = datetime.now(timezone.utc)
        service.last_check = datetime.now(timezone.utc)
        service.failure_count += 1
        await db.commit()
        return {"status": 503}
