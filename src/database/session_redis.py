from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from config.settings import Settings
from services.service_status_cache import RedisServiceStatusCache

settings = Settings()

redis_client_sync = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


def get_async_redis() -> AsyncRedis:
    return AsyncRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)


async def get_redis_cache():
    return RedisServiceStatusCache(get_async_redis())
