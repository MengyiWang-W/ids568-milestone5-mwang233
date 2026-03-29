# src/caching.py

import hashlib
import json
import time
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from collections import OrderedDict

from .models import InferenceRequest


# ==============================
# Abstract Backend
# ==============================
class CacheBackend(ABC):

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int) -> None:
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def clear(self) -> None:
        pass


# ==============================
# In-Memory Backend (LRU)
# ==============================
class InMemoryBackend(CacheBackend):

    def __init__(self, max_entries: int = 1000):
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.max_entries = max_entries
        self.hits = 0
        self.misses = 0

    async def get(self, key: str) -> Optional[str]:
        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]

        # TTL check
        if time.time() > entry["expire_at"]:
            del self.cache[key]
            self.misses += 1
            return None

        # ✅ LRU: move to end
        self.cache.move_to_end(key)

        self.hits += 1
        print(f"[CACHE] hit key={key[:8]}")

        return entry["value"]

    async def set(self, key: str, value: str, ttl: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)

        elif len(self.cache) >= self.max_entries:
            evicted_key, _ = self.cache.popitem(last=False)
            print(f"[CACHE] evict key={evicted_key[:8]}")

        self.cache[key] = {
            "value": value,
            "expire_at": time.time() + ttl,
        }

    async def clear(self) -> None:
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0,
            "total_entries": len(self.cache),
            "backend": "in_memory",
            "eviction_policy": "LRU",
        }


# ==============================
# Redis Backend
# ==============================
class RedisBackend(CacheBackend):

    def __init__(self, redis_url: str):
        import redis.asyncio as redis
        self.redis = redis.from_url(redis_url)
        self.hits = 0
        self.misses = 0

    async def get(self, key: str) -> Optional[str]:
        value = await self.redis.get(key)
        if value:
            self.hits += 1
            print(f"[CACHE] hit (redis)")
            return value.decode()

        self.misses += 1
        return None

    async def set(self, key: str, value: str, ttl: int) -> None:
        await self.redis.setex(key, ttl, value)

    async def clear(self) -> None:
        await self.redis.flushdb()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0,
            "total_entries": -1,  # Redis unknown
            "backend": "redis",
            "eviction_policy": "redis-managed",
        }


# ==============================
# LLM Cache Layer
# ==============================
class LLMCache:

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 3600,
        max_entries: int = 10000,
        use_redis: bool = False,
    ):
        self.default_ttl = default_ttl

        if use_redis:
            try:
                self.backend = RedisBackend(redis_url or "redis://localhost:6379")
                print("[CACHE] using Redis backend")
            except Exception:
                print("[CACHE] Redis failed → fallback to in-memory")
                self.backend = InMemoryBackend(max_entries)
        else:
            self.backend = InMemoryBackend(max_entries)

    # ==============================
    # Key normalization
    # ==============================
    def _normalize_prompt(self, text: str) -> str:
        return " ".join(text.lower().strip().split())

    def _make_key(self, request: InferenceRequest) -> str:
        key_data = {
            "prompt": self._normalize_prompt(request.prompt),
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        content = json.dumps(key_data, sort_keys=True)
        return f"llm:{hashlib.sha256(content.encode()).hexdigest()[:32]}"

    # ==============================
    # Get
    # ==============================
    async def get(self, request: InferenceRequest) -> Optional[str]:
        if request.temperature > 0:
            return None

        key = self._make_key(request)
        return await self.backend.get(key)

    # ==============================
    # Set
    # ==============================
    async def set(
        self,
        request: InferenceRequest,
        response: str,
        ttl: Optional[int] = None,
    ) -> None:
        if request.temperature > 0:
            return

        key = self._make_key(request)
        await self.backend.set(key, response, ttl or self.default_ttl)

    async def clear(self) -> None:
        await self.backend.clear()

    def get_stats(self) -> Dict[str, Any]:
        return self.backend.get_stats()