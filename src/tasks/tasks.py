from datetime import timedelta, timezone, datetime

from sqlalchemy import select, or_
from config.settings import Settings
from database.models.circuit_breaker import MonitoredServices
from services.service_status_cache import RedisServiceStatusCache
from services.redis_pubsub_manager import redis_pubsub_manager
from scheduler.rq_sheduler import queue
from tasks.db import get_session_factory, get_redis_client
from tasks.monitoring import check_service_availability

settings = Settings()


async def run_monitoring_and_notify_job():
    await run_all_monitoring_checks()
    redis_client = get_redis_client()
    try:
        redis_pubsub_manager.redis_client = redis_client
        await redis_pubsub_manager.publish()
    finally:
        await redis_client.aclose()


async def run_all_monitoring_checks():
    async with get_session_factory()() as db:
        time_distance = datetime.now(timezone.utc) - timedelta(
            seconds=settings.TIMEOUT_CHECK_SERVICES)
        services = await db.execute(select(MonitoredServices.id).where(or_(MonitoredServices.last_check == None,
                                                                           MonitoredServices.last_check < time_distance)))
        services_ids = services.scalars().all()
    for s_id in services_ids:
        queue.enqueue(check_service_availability_task, s_id, job_timeout=60)


async def check_service_availability_task(service_id: int):
    async_redis = get_redis_client()
    redis_cache_service = RedisServiceStatusCache(async_redis)
    async with get_session_factory()() as db:
        service = await db.get(MonitoredServices, service_id)
        if service:
            try:
                await check_service_availability(service, db, redis_cache_service)
                await db.commit()
            except Exception as e:
                await db.rollback()
                raise e
            finally:
                await async_redis.aclose()
