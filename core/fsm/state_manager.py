import os, json, redis.asyncio as redis  # <- usa redis-py assíncrono

TTL = 3600
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

# conexão global
r = redis.from_url(f"redis://{REDIS_HOST}", decode_responses=True)

async def get_state(phone: str):
    data = await r.get(f"wg:{phone}:state")
    return json.loads(data) if data else None

async def set_state(phone: str, step: str, data: dict | None = None):
    await r.setex(f"wg:{phone}:state", TTL,
                  json.dumps({"step": step, "data": data or {}}))
