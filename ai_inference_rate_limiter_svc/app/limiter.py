import time
import os
import logging
from redis import Redis
from redis.exceptions import ConnectionError, RedisError

from .config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.upper())

# Constant values reading from settings
WINDOW_DURATION_MS = settings.WINDOW_DURATION_SECONDS * 1000
TTL_SECONDS = settings.WINDOW_DURATION_SECONDS + settings.TTL_BUFFER_SECONDS
DEFAULT_MAX_REQUESTS = settings.DEFAULT_MAX_REQUESTS

class DistributedRateLimiter:
    """
    The below code is service layer for the rate limiting, 
    it manages the Redis connection and Lua script execution
    """
    
    def __init__(self):
        self.redis_client = Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            decode_responses=True,
            socket_timeout=5
        )
        self.lua_script_sha = self._load_lua_script()
        self._check_connection()
        logger.info("DistributedRateLimiter initialized successfully.")

    def _check_connection(self):
        try:
            self.redis_client.ping()
        except ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            raise ConnectionError("Could not connect to Redis. Ratelimiter not available.")

    def _load_lua_script(self) -> str:
        try:
            script_path = os.path.join(os.path.dirname(__file__), '..', 'lua_scripts', 'sliding_window.lua')
            with open(script_path, 'r') as f:
                script_content = f.read()
            return self.redis_client.script_load(script_content)
        except RedisError as e:
            logger.error(f"Failed to load Lua script into Redis: {e}")
            raise e
        except FileNotFoundError as e:
            logger.error(f"Lua script file not found: {e}")
            raise e

    def allow(self, user_id: str, model_id: str, max_limit: int = DEFAULT_MAX_REQUESTS) -> bool:
        key = f"rl:{user_id}:{model_id}"
        
        current_time_ms = int(time.time() * 1000)
        window_start_time_ms = current_time_ms - WINDOW_DURATION_MS
        
        try:
            result = self.redis_client.evalsha(
                self.lua_script_sha, 
                1, 
                key, 
                current_time_ms, 
                window_start_time_ms, 
                max_limit, 
                TTL_SECONDS
            )
            return result == 1
        except RedisError as e:
            logger.error(f"Redis command failed during evaluation. Error: {e}")
            return True