from __future__ import annotations

import time
from typing import Optional
from redis.asyncio import Redis
import structlog

logger = structlog.get_logger(__name__)


class RedisRateLimiter:
    """Distributed rate limiter using Redis with sliding window."""

    def __init__(
        self,
        redis_client: Redis,
        max_requests: int = 60,
        window_seconds: int = 60,
        key_prefix: str = "ratelimit",
    ):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    async def is_allowed(
        self,
        identifier: str,
        endpoint: Optional[str] = None,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ) -> tuple[bool, int]:
        """
        Check if request is allowed.

        Args:
            identifier: Unique identifier (e.g., IP address)
            endpoint: Optional endpoint name
            max_requests: Override default max_requests
            window_seconds: Override default window_seconds

        Returns:
            (is_allowed, retry_after_seconds)
        """
        # Use custom limits if provided, otherwise use defaults
        max_req = max_requests if max_requests is not None else self.max_requests
        window_sec = window_seconds if window_seconds is not None else self.window_seconds

        key = f"{self.key_prefix}:{identifier}"
        if endpoint:
            key = f"{key}:{endpoint}"

        now = time.time()
        window_start = now - window_sec

        pipe = self.redis.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count requests in window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiry
        pipe.expire(key, window_sec)

        results = await pipe.execute()
        request_count = results[1]

        if request_count >= max_req:
            # Get oldest request timestamp
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(window_sec - (now - oldest[0][1])) + 1
                return False, retry_after
            return False, window_sec

        return True, 0

    async def reset(self, identifier: str, endpoint: Optional[str] = None):
        """Reset rate limit for identifier."""
        key = f"{self.key_prefix}:{identifier}"
        if endpoint:
            key = f"{key}:{endpoint}"
        await self.redis.delete(key)
