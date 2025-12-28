import asyncio
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from rq_dashboard_fast import RedisQueueDashboard

from config.settings import Settings
from tasks.tasks import run_all_monitoring_checks
from views import service_monitoring_router
from sheduler.rq_sheduler import scheduler, queue

settings = Settings()


def run_all_monitoring_checks_sync():
    asyncio.run(run_all_monitoring_checks())


@asynccontextmanager
async def lifespan(_: FastAPI):
    for job in scheduler.get_jobs():
        scheduler.cancel(job)

    scheduler.schedule(scheduled_time=datetime.now(timezone.utc),
                       func=run_all_monitoring_checks_sync,
                       interval=15,
                       result_ttl=120,
                       repeat=None)
    print("Scheduler started!🚀")
    yield


app = FastAPI(lifespan=lifespan)

api_version_prefix = "/api/v1"
dashboard = RedisQueueDashboard("redis://localhost:6379", "/rq")
app.mount("/rq", dashboard)
app.include_router(service_monitoring_router, prefix=api_version_prefix, tags=["service_monitoring"])
