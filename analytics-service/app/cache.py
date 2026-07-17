import os
import logging
import json

logger = logging.getLogger("marketmind.cache")

# Dynamic Redis connection with grace fallback
try:
    import redis
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True, socket_timeout=1.0)
    # Test ping
    redis_client.ping()
    REDIS_ACTIVE = True
    logger.info(f"Successfully connected to Redis cache cluster at {redis_host}:{redis_port}")
except Exception as e:
    logger.warning(f"Redis cache server is offline ({e}). Operating in pass-through database query mode.")
    redis_client = None
    REDIS_ACTIVE = False

def get_cached(key: str):
    if not REDIS_ACTIVE or not redis_client:
        return None
    try:
        data = redis_client.get(key)
        if data:
            logger.info(f"Cache HIT for key: {key}")
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Failed to read from Redis cache: {e}")
    return None

def set_cached(key: str, value, expire_seconds=300):
    if not REDIS_ACTIVE or not redis_client:
        return
    try:
        logger.info(f"Caching value for key: {key} (expiry: {expire_seconds}s)")
        redis_client.set(key, json.dumps(value), ex=expire_seconds)
    except Exception as e:
        logger.warning(f"Failed to write to Redis cache: {e}")
