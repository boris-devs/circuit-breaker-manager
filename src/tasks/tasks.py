from datetime import timedelta, timezone, datetime

from sqlalchemy import select, NullPool, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config.settings import Settings
from database.models.circuit_breaker import MonitoredServices
from database.session_postgresql import POSTGRESQL_DATABASE_URL
from sheduler.rq_sheduler import queue
from tasks.monitoring import check_service_availability

settings = Settings()


async def run_all_monitoring_checks():
    postgresql_engine = create_async_engine(url=POSTGRESQL_DATABASE_URL, echo=True, poolclass=NullPool)
    async_postgresql_session = async_sessionmaker(
        bind=postgresql_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    try:
        async with async_postgresql_session() as db:
            time_distance = datetime.now(timezone.utc) - timedelta(
                seconds=settings.TIMEOUT_CHECK_SERVICES)
            services = await db.execute(select(MonitoredServices).where(or_(MonitoredServices.last_check == None,
                                                                        MonitoredServices.last_check < time_distance)))

            for service in services.scalars():
                print(f"Checking service {service.name}")
                queue.enqueue(check_service_availability_task, service.id)
    finally:
        await postgresql_engine.dispose()


async def check_service_availability_task(service_id: int):
    postgresql_engine = create_async_engine(url=POSTGRESQL_DATABASE_URL, echo=True, poolclass=NullPool)
    async_postgresql_session = async_sessionmaker(
        bind=postgresql_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
    )
    try:
        async with async_postgresql_session() as db:
            service = await db.get(MonitoredServices, service_id)
            if service:
                await check_service_availability(service, db)
    finally:
        await postgresql_engine.dispose()
