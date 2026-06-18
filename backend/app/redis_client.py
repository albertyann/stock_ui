"""Redis client wrapper with graceful degradation.

Single-module API:
    from app.redis_client import cache_json, get_cached_json, get_redis

If Redis is unavailable, all operations silently return False / None so the
caller can fall back to the original (uncached) code path. This keeps the
indicator-calc feature from breaking the rest of the backend when Redis is
down or not installed.
"""

import json
import logging
from typing import Any, Optional

import redis

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Return a process-wide Redis client singleton, or None if unavailable.

    Each call reconnects lazily after a failure, so a transient Redis outage
    is recovered automatically once Redis comes back.
    """
    global _client
    if _client is not None:
        return _client
    try:
        settings = get_settings()
        client = redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        _client = client
        logger.info("Redis connected: %s", settings.redis_url)
        return _client
    except Exception as e:
        logger.warning("Redis unavailable, caching disabled: %s", e)
        return None


def cache_json(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Serialize value as JSON and write to Redis. Returns True on success."""
    client = get_redis()
    if client is None:
        return False
    try:
        payload = json.dumps(value, ensure_ascii=False, default=str)
        client.set(key, payload, ex=ttl)
        return True
    except Exception as e:
        logger.warning("Redis write failed for %s: %s", key, e)
        return False


def get_cached_json(key: str) -> Optional[Any]:
    """Read and JSON-decode a key. Returns None if missing, unavailable, or invalid."""
    client = get_redis()
    if client is None:
        return None
    try:
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning("Redis read failed for %s: %s", key, e)
        return None
