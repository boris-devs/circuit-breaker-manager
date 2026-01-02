import redis.asyncio as aioredis
import json


class RedisPubSubManager:

    def __init__(self, redis_client: aioredis.Redis | None = None):
        self.redis_client = redis_client
        self.channel = "service_status_channel"

    @property
    def pubsub(self):
        return self.redis_client.pubsub()

    async def publish(self):
        if not self.redis_client:
            raise RuntimeError("Redis client is not set in RedisPubSubManager")
        await self.redis_client.publish("service_status_channel", "updated")

    async def get_cached_statuses(self):
        if not self.redis_client:
            return []
        keys = []
        async for key in self.redis_client.scan_iter("service_status:*"):
            keys.append(key)

        if not keys:
            return []

        values = await self.redis_client.mget(keys)
        return [json.loads(v) for v in values if v]

    async def start_listener(self, ws_manager):
        if not self.redis_client:
            raise RuntimeError("Redis client is not set in RedisPubSubManager")
        try:
            async with self.redis_client.pubsub() as pubsub:
                await pubsub.subscribe(self.channel)

                async for message in pubsub.listen():
                    print(f"RAW MESSAGE: {message}")

                    if message["type"] == "message":
                        data = message["data"]
                        print(f"Data received: {data}")

                        state = await self.get_cached_statuses()
                        await ws_manager.broadcast({
                            "type": "update",
                            "data": state
                        })
        except Exception as e:
            print(f"Error {e}")

redis_pubsub_manager = RedisPubSubManager()
