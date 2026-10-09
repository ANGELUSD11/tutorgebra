import os
import time
import uuid
import logging
from fastapi import HTTPException
import redis.asyncio as redis

logger = logging.getLogger('TutorGebraRedis')

# Global Redis client instance
redis_client = None

async def init_redis():
    """Initialize Redis connection using the REDIS_URL environment variable."""
    global redis_client
    # In Railway, when you add the plugin, you'll be provided with a URL like redis://default:password@host:port
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    
    try:
        redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        # Ping to verify successful connection
        await redis_client.ping()
        logger.info("Successfully connected to Redis for Global Rate Limiting!")
    except Exception as e:
        logger.warning(f"Could not connect to Redis. Check if the service is running: {e}")
        redis_client = None

async def close_redis():
    """Close connection on server shutdown."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

async def check_rate_limit_redis(client_ip: str, limit: int = 5, window: int = 60) -> bool:
    """
    Verify if an IP has exceeded the request limit using a Sliding Window Log
    algorithm with Redis Sorted Sets (ZSET).
    
    Returns True if Redis successfully handled the validation.
    Returns False if Redis is offline or failed (to trigger local fallback).
    """
    if not redis_client:
        # If Redis is unavailable, log a warning to use the memory fallback.
        logger.warning(f"Redis is offline. Falling back to local memory limit for IP: {client_ip}")
        return False

    key = f"rate_limit:{client_ip}"
    now = time.time()
    window_start = now - window
    member = f"{now}:{uuid.uuid4()}"

    # Use a pipeline to execute all operations atomically
    async with redis_client.pipeline(transaction=True) as pipe:
        try:
            # 1. Remove old requests that fall outside the time window
            pipe.zremrangebyscore(key, 0, window_start)
            
            # 2. Count how many requests remain in the current window
            pipe.zcard(key)
            
            # 3. Add the current request
            pipe.zadd(key, {member: now})
            
            # 4. Refresh key expiration to free memory
            pipe.expire(key, window)
            
            # Execute transaction
            results = await pipe.execute()
            
            # results[1] is the result of zcard BEFORE adding the current request
            request_count = results[1]
            
            if request_count >= limit:
                logger.warning(f"Global Rate limit exceeded for IP: {client_ip}")
                raise HTTPException(
                    status_code=429, 
                    detail="Too many requests. Please wait a minute before generating another lesson."
                )
            
            # Redis worked and the request is allowed
            return True
                
        except redis.RedisError as e:
            logger.error(f"Redis error during rate limiting: {e}. Falling back to memory.")
            # If Redis fails for a second, warn to use fallback.
            return False

