
from rq import Queue
from rq_scheduler import Scheduler
from database.session_redis import redis_client_sync


queue = Queue(connection=redis_client_sync)
scheduler = Scheduler(queue=queue, connection=redis_client_sync)
