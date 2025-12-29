from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from config.settings import Settings
from services.cache_service import CacheCircuitBreakerService

settings = Settings()
redis_client_sync = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
redis_client_async = AsyncRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)


async def get_redis_cache():
    return CacheCircuitBreakerService(redis_client_async)
