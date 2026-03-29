# src/server.py

from fastapi import FastAPI

from .models import (
    InferenceRequest,
    InferenceResponse,
    MetricsResponse,
    BatchStats,
    CacheStats,
)
from .inference import ModelManager
from .caching import LLMCache
from .batching import DynamicBatcher
from .config import settings

app = FastAPI(title="LLM Inference Service")

# =========================
# Init helpers
# =========================
def create_model() -> ModelManager:
    return ModelManager(settings.model_name)


def create_cache() -> LLMCache:
    return LLMCache(
        redis_url=settings.redis_url,
        default_ttl=settings.cache_ttl_seconds,
        max_entries=settings.cache_max_entries,
        use_redis=settings.use_redis,
    )


def create_batcher(model: ModelManager) -> DynamicBatcher:
    return DynamicBatcher(
        max_batch_size=settings.max_batch_size,
        max_wait_ms=settings.batch_timeout_ms,
        model_manager=model,
    )


# Global instances
model = create_model()
cache = create_cache()
batcher = create_batcher(model)


# =========================
# Startup / Shutdown
# =========================
@app.on_event("startup")
async def startup():
    await model.load()
    await batcher.start()


@app.on_event("shutdown")
async def shutdown():
    await batcher.stop()


# =========================
# Baseline Endpoint
# No batching, no caching
# =========================
@app.post("/generate_baseline", response_model=InferenceResponse)
async def generate_baseline(req: InferenceRequest):
    result = await model.generate(
        prompt=req.prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    return InferenceResponse(text=result, cached=False)


# =========================
# Optimized Endpoint
# With batching + caching
# =========================
@app.post("/generate", response_model=InferenceResponse)
async def generate(req: InferenceRequest):
    # 1. Cache lookup
    cached_value = await cache.get(req)
    if cached_value is not None:
        return InferenceResponse(text=cached_value, cached=True)

    # 2. Dynamic batching
    result = await batcher.submit(req)

    # 3. Cache write-back
    await cache.set(req, result)

    return InferenceResponse(text=result, cached=False)


# =========================
# Metrics
# =========================
@app.get("/metrics", response_model=MetricsResponse)
async def metrics():
    cache_stats_raw = cache.get_stats()
    batch_stats_raw = batcher.get_stats()

    batch_stats = BatchStats(
        total_requests=batch_stats_raw.get("total_requests", 0),
        batches_processed=batch_stats_raw.get("batches_processed", 0),
        avg_batch_size=batch_stats_raw.get("avg_batch_size", 0.0),
        avg_wait_time_ms=batch_stats_raw.get("avg_wait_time_ms", 0.0),
    )

    cache_stats = CacheStats(
        hits=cache_stats_raw.get("hits", 0),
        misses=cache_stats_raw.get("misses", 0),
        hit_rate=cache_stats_raw.get("hit_rate", 0.0),
        total_entries=cache_stats_raw.get("total_entries", 0),
        backend="redis" if settings.use_redis else "in_memory",
        eviction_policy="LRU",
        cache_enabled=True,
    )

    return MetricsResponse(cache=cache_stats, batcher=batch_stats)


# =========================
# Reset Endpoints
# Used by benchmark
# =========================
@app.post("/reset")
@app.post("/reset_cache")
async def reset():
    """
    Reset cache and batching state to avoid benchmark contamination.
    Recreates the batcher so internal queue and stats return to zero.
    """
    global batcher

    await batcher.stop()
    await cache.clear()

    batcher = create_batcher(model)
    await batcher.start()

    return {"status": "ok"}


# =========================
# Health
# =========================
@app.get("/")
async def root():
    return {"status": "running"}