from sqlalchemy.ext.asyncio import AsyncSession

from database.models.circuit_breaker import MonitoredServices, StateServiceEnum, CircuitBreakerLog
from schemas.monitoring import CreateServiceMonitoringSchema, CreateCircuitBreakerLogsSchema


async def create_service(service_in: CreateServiceMonitoringSchema, db: AsyncSession):
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


async def service_create_logs(
        db: AsyncSession,
        service_id: int,
        old_state: StateServiceEnum,
        new_state: StateServiceEnum,
        detail: str | None = None
):
    log_data = CreateCircuitBreakerLogsSchema(service_id=service_id,
                                              old_state=old_state,
                                              new_state=new_state,
                                              detail=detail)
    log = CircuitBreakerLog(**log_data.model_dump())
    db.add(log)
