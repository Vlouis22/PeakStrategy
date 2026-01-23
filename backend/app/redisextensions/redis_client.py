# backend/app/redisextensions/redis_client.py
import redis
import os
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True  # store strings, not bytes
)

def redis_get_json(key: str):
    value = redis_client.get(key)
    if value:
        return json.loads(value)
    return None

def redis_set_json(key: str, value, ttl: int):
    redis_client.setex(key, ttl, json.dumps(value))

# Test connection on import
try:
    redis_client.ping()
    print("✅ Redis connection successful!")
except redis.ConnectionError:
    print("❌ Redis connection failed. Make sure Redis server is running.")