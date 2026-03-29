##  LLM Inference Server with Batching and Caching

This project implements a high-throughput LLM inference service using FastAPI, enhanced with dynamic batching and response caching.

The system is designed to simulate production-style LLM serving and evaluate performance trade-offs between latency, throughput, and cache effectiveness.

## 1. Features
Baseline inference (no batching, no caching)
Dynamic batching (queue + timeout)
LRU caching with TTL
Cache-aware request handling
Benchmarking under different concurrency levels
Metrics tracking (latency, throughput, cache hit rate)

## 2. System Architecture
Baseline Pipeline

Request → Model → Response

Each request processed independently
No batching
No caching
Optimized Pipeline

Request → Cache Lookup
↓
(hit) return cached response
↓
(miss) → Batch Queue → Model → Cache Write → Response

Key components:

Dynamic batching (group requests for efficiency)
Cache lookup before inference
Cache write-back after inference

## 3. Installation
Prerequisites
Python 3.10+
pip
(Optional) Redis for distributed caching
Install dependencies

pip install -r requirements.txt

## 4. Configuration

Copy environment template:

cp .env.example .env

Key parameters:

LLM_MAX_BATCH_SIZE
LLM_BATCH_TIMEOUT_MS
LLM_CACHE_TTL_SECONDS
LLM_CACHE_MAX_ENTRIES

## 5. Running the Server
Development mode

uvicorn src.server --reload

Production-style mode

uvicorn src.server --host 0.0.0.0 --port 8000

## 6. API Endpoints
Baseline

POST /generate_baseline

No batching
No caching
Optimized

POST /generate

Cache lookup
Batch execution on miss
Cache write-back
Health Check

GET /health

Metrics

GET /metrics

## 7. Example Usage
Optimized request

curl -X POST http://127.0.0.1:8000/generate
-H "Content-Type: application/json"
-d "{"prompt":"Explain AI","max_tokens":128,"temperature":0.0}"

Baseline request

curl -X POST http://127.0.0.1:8000/generate_baseline
-H "Content-Type: application/json"
-d "{"prompt":"Explain AI","max_tokens":128,"temperature":0.0}"

## 8. Running Benchmarks

From project root:

python -m benchmarks.run_benchmarks

Optional arguments:

python -m benchmarks.run_benchmarks
--base-url http://127.0.0.1:8000
--num-requests 50
--low-concurrency 10
--medium-concurrency 50
--high-concurrency 100

# 8.1 Benchmark Methodology (IMPORTANT)

To ensure reproducibility and fair comparison:

Warm-up phase: 5 requests (excluded from metrics)
Measurement phase: 50 requests per test
Concurrency levels:
Low: 10 concurrent requests
Medium: 50 concurrent requests
High: 100 concurrent requests

Cache evaluation:

Cold cache: cache cleared before measurement
Warm cache: repeated prompts used to ensure cache hits

Metrics collected:

Average latency (ms)
P50 / P95 latency (ms)
Throughput (requests/sec)
Cache hit rate

This ensures consistent and reproducible performance measurements.

## 9. Benchmark Results

Latest measured results:

Baseline
Avg latency: 94.71 ms
Throughput: 10.56 req/s
Cache hit rate: 0.0
Low Concurrency
Avg latency: 36.92 ms
Throughput: 131.19 req/s
Cache hit rate: 0.9
Medium Concurrency
Avg latency: 34.54 ms
Throughput: 263.97 req/s
Cache hit rate: 1.0
High Concurrency
Avg latency: 59.55 ms
Throughput: 262.50 req/s
Cache hit rate: 1.0
Cache Performance
Cold latency: 203.62 ms
Warm latency: 13.25 ms
Speedup: ~15.37×
Cold hit rate: 0.0
Warm hit rate: 1.0
Key Observations
Throughput improves significantly (~25× increase from baseline to medium)
Latency decreases under batching at low and medium concurrency
Throughput plateaus at high concurrency, indicating system saturation
Cache dramatically reduces latency (~15× speedup)
System exhibits non-linear scaling behavior

## 10. Design Decisions
Batching
Improves throughput by amortizing model cost
Multiple requests share a single forward pass (compute reuse)
Introduces queue delay under high load
Caching
Eliminates redundant computation entirely
Only applied to deterministic requests (temperature = 0.0)
Returns responses in constant time (O(1))

# 10.1 Trade-off Analysis (CRITICAL)

Batching trade-off:

Larger batch size → higher throughput
But longer waiting time → increased latency

Caching trade-off:

Larger cache → higher hit rate
But increased memory usage

System behavior:

Medium concurrency achieves optimal balance
High concurrency leads to saturation (queue delay dominates)

# 10.2 Why Performance Improves (Compute Pathway Explanation)

Baseline:

Each request triggers a full model execution

Batching:

Multiple requests share a single forward pass
Reduces per-request compute overhead

Caching:

Repeated requests bypass model entirely
Eliminates computation and reduces latency dramatically

## 11. Reproducibility

This repository includes:

Benchmark script (benchmarks/run_benchmarks.py)
Raw results (benchmarks/results/results.json)
Environment configuration (.env.example)
Modular code structure

# 11.1 Quick Reproduction (Under 5 Minutes)
Install dependencies:

pip install -r requirements.txt

Start server:

uvicorn src.server --host 127.0.0.1 --port 8000

Run benchmarks:

python -m benchmarks.run_benchmarks

(Optional) Generate charts:

python analysis/visualizations/generate_charts.py

## 12. Governance Considerations

This system includes:

SHA-256 hashed cache keys (no plaintext identifiers)
TTL-based expiration
Bounded cache size
Deterministic-only caching

Risks:

Cached responses may contain sensitive content
No rate limiting or access control

Future improvements:

Rate limiting
Authentication
Cache invalidation APIs
Input/output moderation

##  13. Limitations
Performance depends on workload characteristics
Cache effectiveness depends on repetition
System saturates under high concurrency
No distributed scaling implemented

## 14. Conclusion

This project demonstrates:

Dynamic batching significantly improves throughput (~25×)
Caching reduces latency dramatically (~15×)
The system exhibits realistic saturation behavior

LLM serving systems require balancing latency, throughput, and cache effectiveness, and must be tuned based on workload patterns.