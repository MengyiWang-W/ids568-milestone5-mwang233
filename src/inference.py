"""
Mock LLM inference layer.

Used for benchmarking batching and caching performance.
"""

import asyncio
from typing import List


class ModelManager:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.is_loaded = False

    async def load(self):
        """Simulate model loading."""
        await asyncio.sleep(0.1)
        self.is_loaded = True
        print(f"[MODEL] loaded model={self.model_name}")

    # =========================
    # Single inference
    # =========================
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> str:
        """
        Baseline single request inference.

        Simulates fixed latency per request.
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        # baseline latency
        await asyncio.sleep(0.08)

        return f"[{self.model_name}] Response to: {prompt[:60]}..."

    # =========================
    # Batch inference
    # =========================
    async def generate_batch(self, prompts: List[str]) -> List[str]:
        """
        Batched inference.

        Key idea:
        - shared overhead (model forward pass setup)
        - marginal cost per request

        So:
        total_latency = base_cost + per_item_cost * batch_size
        """

        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        batch_size = len(prompts)

        print(f"[MODEL] batch inference size={batch_size}")

        # More realistic latency model:
        base_cost = 0.06        # shared overhead
        per_item_cost = 0.01    # marginal cost per request

        await asyncio.sleep(base_cost + per_item_cost * batch_size)

        return [
            f"[{self.model_name}] Response to: {p[:60]}..."
            for p in prompts
        ]