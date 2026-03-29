"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field, ConfigDict


# =========================
# Request / Response
# =========================
class InferenceRequest(BaseModel):
    """
    Request schema for text generation.
    """

    model_config = ConfigDict(protected_namespaces=())

    prompt: str = Field(
        ...,
        description="Input prompt text",
        min_length=1,
        max_length=4096,
        examples=["Explain batching in LLM serving"],
    )

    max_tokens: int = Field(
        default=256,
        ge=1,
        le=2048,
        description="Maximum tokens to generate",
    )

    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description=(
            "Sampling temperature. "
            "Only temperature=0 responses are cached (deterministic)."
        ),
    )


class InferenceResponse(BaseModel):
    """
    Response schema.
    """

    text: str = Field(description="Generated response text")
    cached: bool = Field(
        default=False,
        description="Indicates whether response was served from cache",
    )


# =========================
# Metrics Schemas
# =========================
class BatchStats(BaseModel):
    """
    Batching performance metrics.
    """

    total_requests: int = Field(ge=0)
    batches_processed: int = Field(ge=0)

    avg_batch_size: float = Field(
        ge=0,
        description="Average number of requests per batch",
    )

    avg_wait_time_ms: float = Field(
        ge=0,
        description="Average time requests waited in queue before processing (ms)",
    )


class CacheStats(BaseModel):
    """
    Cache performance metrics.
    """

    hits: int = Field(ge=0)
    misses: int = Field(ge=0)

    hit_rate: float = Field(
        ge=0,
        le=1,
        description="Cache hit ratio",
    )

    total_entries: int = Field(
        ge=-1,
        description="Number of cached items (-1 if unknown, e.g. Redis)",
    )

    backend: str = Field(
        description="Cache backend type (in_memory or redis)"
    )

    eviction_policy: str = Field(
        description="Cache eviction policy (LRU or redis-managed)"
    )

    cache_enabled: bool = Field(
        description="Indicates if caching is enabled"
    )

class MetricsResponse(BaseModel):
    """
    Combined metrics response.
    """
    cache: CacheStats
    batcher: BatchStats