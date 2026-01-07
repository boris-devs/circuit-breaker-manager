import asyncio
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from rq_dashboard_fast import RedisQueueDashboard

from config.settings import Settings
from database import redis_async_client
from services.redis_pubsub_manager import redis_pubsub_manager
from services.websocket_manager import ws_manager
from tasks.tasks import run_monitoring_and_notify_job
from views import service_monitoring_router
from scheduler.rq_sheduler import scheduler

settings = Settings()
app = FastAPI()

instrumentator = Instrumentator().instrument(app)


@asynccontextmanager
async def lifespan(_: FastAPI):
    for job in scheduler.get_jobs():
        scheduler.cancel(job)

    instrumentator.expose(app)

    redis_pubsub_manager.redis_client = redis_async_client()
    scheduler.schedule(scheduled_time=datetime.now(timezone.utc),
                       func=run_monitoring_and_notify_job,
                       interval=15,
                       result_ttl=30,
                       repeat=None)
    print("Scheduler started!🚀")

    pubsub_task = asyncio.create_task(
        redis_pubsub_manager.start_listener(ws_manager)
    )

    yield

    pubsub_task.cancel()


app.router.lifespan_context = lifespan

api_version_prefix = "/api/v1"

dashboard = RedisQueueDashboard(settings.redis_url, "/rq")
app.mount("/rq", dashboard)
app.include_router(service_monitoring_router, prefix=api_version_prefix, tags=["service_monitoring"])
