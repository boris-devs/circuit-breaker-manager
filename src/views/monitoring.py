from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from repository.monitoring_repository import create_service_monitoring, get_service, check_health_service
from schemas.monitoring import CreateServiceMonitoringSchema, CreateServiceMonitoringResponseSchema
from tasks.tasks import redis_client
from services.redis_cache import CircuitBreakerCache
from database.models.circuit_breaker import StateServiceEnum

router = APIRouter()


@router.post("/register_service/", response_model=CreateServiceMonitoringResponseSchema)
async def register_service(new_service: CreateServiceMonitoringSchema, db: AsyncSession = Depends(get_db)):
    created_service = await create_service_monitoring(new_service, db)
    if new_service.state == StateServiceEnum.OPEN:
        ...

        #
    return created_service

@router.get("/health/{service_id}")
async def get_state_service(service_id: int, db: AsyncSession = Depends(get_db)):
    """Возвращает текущее состояние circuit breaker сервиса.

    Источником является Redis-кэш (если есть), иначе БД. Без сетевых проверок.
    """
    service = await get_service(service_id, db)
    if not service:
        return {"status": 404, "message": "Service not found"}

    cache = CircuitBreakerCache(redis_client)
    r_state, r_fail, r_open_until = cache.get_state(service_id)

    if r_state is None:
        state_str = service.state.value if isinstance(service.state, StateServiceEnum) else str(service.state)
        fail_count = service.failure_count or 0
        open_until_ts = int(service.last_failure_time.timestamp()) if service.last_failure_time else None
    else:
        state_str = r_state
        fail_count = r_fail
        open_until_ts = r_open_until


    from datetime import datetime
    now_ts = int(datetime.utcnow().timestamp())
    allowed = not (state_str == StateServiceEnum.OPEN.value and open_until_ts and now_ts < open_until_ts)

    return {
        "status": 200,
        "service_id": service.id,
        "name": service.name,
        "url": service.url,
        "state": state_str,
        "failure_count": fail_count,
        "open_until": open_until_ts,  # unix ts или null
        "last_check": service.last_check.isoformat() if service.last_check else None,
        "allowed_now": allowed,
    }