from redis.asyncio import Redis


async def set_value(client: Redis, key: str, value: str, ttl_seconds: int) -> None:
    await client.set(key, value, ex=ttl_seconds)


async def get_value(client: Redis, key: str) -> str | None:
    return await client.get(key)


async def delete_value(client: Redis, key: str) -> None:
    await client.delete(key)
