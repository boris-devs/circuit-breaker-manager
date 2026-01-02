import json

import redis.asyncio as aioredis

from database.models.circuit_breaker import MonitoredServices
from schemas.monitoring import HealthServiceMonitoringSchema


class CacheCircuitBreakerService:
    def __init__(self, redis_client:  aioredis.Redis):
        self.redis_client = redis_client

    async def get_service_status(self, service_id: int) -> dict | None:
        service = await self.redis_client.get(f"service_status:{service_id}")
        return json.loads(service) if service else None

    async def set_service_status(self, service_id: int, service_data: MonitoredServices):
        schema_data = HealthServiceMonitoringSchema.model_validate(service_data)
        json_data = schema_data.model_dump_json()
        await self.redis_client.set(f"service_status:{service_id}", json_data, ex=30)
