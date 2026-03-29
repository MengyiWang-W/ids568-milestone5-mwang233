"""
Configuration for batching, caching, and model.
"""
from pydantic import BaseModel, Field, ConfigDict

class Settings(BaseModel):
    # ✅ fix protected namespace warning
    model_config = ConfigDict(protected_namespaces=())

    # =========================
    # Model
    # =========================
    model_name: str = Field(default="mock-llm")

    # =========================
    # Batching
    # =========================
    max_batch_size: int = Field(default=8, gt=0)
    batch_timeout_ms: float = Field(default=50.0, gt=0)

    # =========================
    # Caching
    # =========================
    redis_url: str = Field(default="redis://localhost:6379")

    cache_ttl_seconds: int = Field(
        default=30,  # ✅ 比5更合理（benchmark更稳定）
        gt=0
    )

    cache_max_entries: int = Field(
        default=1000,
        gt=0
    )

    use_redis: bool = Field(default=False)

# =========================
# Global settings instance
# =========================
settings = Settings()