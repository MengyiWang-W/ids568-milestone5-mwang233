"""
Dynamic request batching for LLM inference.

Hybrid batching strategy:
- Trigger when batch size reached
- OR timeout exceeded
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any

from .models import InferenceRequest
from .inference import ModelManager


@dataclass
class PendingRequest:
    request: InferenceRequest
    future: asyncio.Future
    arrival_time: float = field(default_factory=time.time)


class DynamicBatcher:
    def __init__(
        self,
        max_batch_size: int = 8,
        max_wait_ms: float = 50.0,
        model_manager: ModelManager | None = None,
    ):
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.model_manager = model_manager

        self.pending: List[PendingRequest] = []
        self.lock = asyncio.Lock()

        self._timeout_task: asyncio.Task | None = None
        self._is_processing = False
        self._running = False

        # stats
        self._total_requests = 0
        self._batches_processed = 0
        self._total_batch_sizes = 0
        self._total_wait_times = 0.0

    # =========================
    # Lifecycle
    # =========================
    async def start(self):
        self._running = True
        self._timeout_task = asyncio.create_task(self._timeout_loop())

    async def stop(self):
        self._running = False
        if self._timeout_task:
            self._timeout_task.cancel()
            try:
                await self._timeout_task
            except asyncio.CancelledError:
                pass

    # =========================
    # Submit request
    # =========================
    async def submit(self, request: InferenceRequest) -> str:
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        pending = PendingRequest(request=request, future=future)

        trigger_batch = False

        async with self.lock:
            self.pending.append(pending)
            self._total_requests += 1

            if len(self.pending) >= self.max_batch_size:
                trigger_batch = True

        if trigger_batch:
            asyncio.create_task(self._safe_process_batch())

        return await future

    # =========================
    # Timeout loop
    # =========================
    async def _timeout_loop(self):
        while self._running:
            await asyncio.sleep(self.max_wait_ms / 1000)

            trigger_batch = False

            async with self.lock:
                if self.pending:
                    oldest = self.pending[0]
                    wait_time = (time.time() - oldest.arrival_time) * 1000

                    if wait_time >= self.max_wait_ms:
                        trigger_batch = True

            if trigger_batch:
                print("[BATCH] timeout triggered")
                asyncio.create_task(self._safe_process_batch())

    # =========================
    # Safe batch processing
    # =========================
    async def _safe_process_batch(self):
        if self._is_processing:
            return

        self._is_processing = True
        try:
            await self._process_batch()
        finally:
            self._is_processing = False

    # =========================
    # Core batch logic
    # =========================
    async def _process_batch(self):
        async with self.lock:
            if not self.pending:
                return

            batch = self.pending[: self.max_batch_size]
            self.pending = self.pending[self.max_batch_size :]

        batch_size = len(batch)
        print(f"[BATCH] processing batch size={batch_size}")

        self._batches_processed += 1
        self._total_batch_sizes += batch_size

        now = time.time()
        for req in batch:
            self._total_wait_times += (now - req.arrival_time) * 1000

        try:
            results = await self._run_inference(batch)
        except Exception as e:
            for pending in batch:
                if not pending.future.done():
                    pending.future.set_exception(e)
            return

        for pending, result in zip(batch, results):
            if not pending.future.done():
                pending.future.set_result(result)

    # =========================
    # Inference
    # =========================
    async def _run_inference(self, batch: List[PendingRequest]) -> List[str]:
        if self.model_manager is None:
            raise RuntimeError("model_manager is not set")

        prompts = [r.request.prompt for r in batch]

        return await self.model_manager.generate_batch(prompts)

    # =========================
    # Stats
    # =========================
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_requests": self._total_requests,
            "batches_processed": self._batches_processed,
            "avg_batch_size": (
                self._total_batch_sizes / self._batches_processed
                if self._batches_processed > 0 else 0
            ),
            "avg_wait_time_ms": (
                self._total_wait_times / self._total_requests
                if self._total_requests > 0 else 0
            ),
        }