from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler

from config.settings import Settings

settings = Settings()

redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

queue = Queue(connection=redis_client)
scheduler = Scheduler(queue=queue, connection=redis_client)
