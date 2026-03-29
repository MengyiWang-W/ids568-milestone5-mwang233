## LLM Inference Server with Batching and Caching

This project implements a high-throughput LLM inference service using FastAPI, enhanced with dynamic batching and response caching.

The system is designed to simulate production-style LLM serving and evaluate performance trade-offs between latency, throughput, and cache effectiveness.

---

## 1. Features

* Baseline inference (no batching, no caching)
* Dynamic batching (queue + timeout)
* LRU caching with TTL
* Cache-aware request handling
* Benchmarking under different concurrency levels
* Metrics tracking (latency, throughput, cache hit rate)

---

## 2. System Architecture

### Baseline Pipeline

Request → Model → Response

* Each request processed independently
* No batching
* No caching

### Optimized Pipeline

Request → Cache Lookup
↓
(hit) return cached response
↓
(miss) → Batch Queue → Model → Cache Write → Response

**Key components:**

* Dynamic batching (group requests for efficiency)
* Cache lookup before inference
* Cache write-back after inference

---

## 3. Installation

### Prerequisites

* Python 3.10+
* pip
* (Optional) Redis for distributed caching

### Install dependencies

pip install -r requirements.txt

---

## 4. Configuration

Copy environment template:

cp .env.example .env

⚠️ IMPORTANT: You must copy the environment file before running the server.

All batching and caching parameters are configurable via this file:

* LLM_MAX_BATCH_SIZE
* LLM_BATCH_TIMEOUT_MS
* LLM_CACHE_TTL_SECONDS
* LLM_CACHE_MAX_ENTRIES

---

## 5. Running the Server

### Development mode

uvicorn src.server --reload

### Production-style mode

uvicorn src.server --host 0.0.0.0 --port 8000

---

## 6. API Endpoints

### Baseline

POST /generate_baseline

* No batching
* No caching

### Optimized

POST /generate

* Cache lookup
* Batch execution on miss
* Cache write-back

### Health Check

GET /health

### Metrics

GET /metrics

---

## 7. Example Usage

### Optimized request

curl -X POST http://127.0.0.1:8000/generate 
-H "Content-Type: application/json" 
-d '{"prompt":"Explain AI","max_tokens":128,"temperature":0.0}'

### Baseline request

curl -X POST http://127.0.0.1:8000/generate_baseline 
-H "Content-Type: application/json" 
-d '{"prompt":"Explain AI","max_tokens":128,"temperature":0.0}'

---

## 8. Running Benchmarks

From project root:

python -m benchmarks.run_benchmarks

### Optional arguments

python -m benchmarks.run_benchmarks 
--base-url http://127.0.0.1:8000 
--num-requests 50

---

## 8.1 Benchmark Methodology (IMPORTANT)

To ensure reproducibility and fair comparison:

* Warm-up phase: 5 requests (excluded)
* Measurement phase: 50 requests per test
* Concurrency levels:

  * Low: 10
  * Medium: 50
  * High: 100

### Cache evaluation

* Cold cache: cache cleared before measurement
* Warm cache: repeated prompts to ensure cache hits

### Metrics collected

* Average latency (ms)
* P50 / P95 latency (ms)
* Throughput (requests/sec)
* Cache hit rate

---

## 9. Benchmark Results

### Baseline

* Avg latency: 94.71 ms
* Throughput: 10.56 req/s
* Cache hit rate: 0.0

### Low Concurrency

* Avg latency: 36.92 ms
* Throughput: 131.19 req/s
* Cache hit rate: 0.9

### Medium Concurrency

* Avg latency: 34.54 ms
* Throughput: 263.97 req/s
* Cache hit rate: 1.0

### High Concurrency

* Avg latency: 59.55 ms
* Throughput: 262.50 req/s
* Cache hit rate: 1.0

### Cache Performance

* Cold latency: 203.62 ms
* Warm latency: 13.25 ms
* Speedup: ~15.37×
* Cold hit rate: 0.0
* Warm hit rate: 1.0

### Key Observations

* Throughput improves significantly (~25×)
* Latency decreases under batching (low/medium)
* Throughput plateaus at high concurrency → system saturation
* Caching reduces latency dramatically (~15×)
* System shows non-linear scaling

---

## 10. Design Decisions

### Batching

* Shares model compute across requests
* Improves throughput
* Introduces queue delay

### Caching

* Eliminates redundant computation
* Only for deterministic requests (temperature = 0.0)
* O(1) response time

---

## 10.1 Trade-off Analysis (CRITICAL)

### Batching

* Larger batch → higher throughput
* But → increased latency

### Caching

* Larger cache → higher hit rate
* But → more memory usage

### System behavior

* Medium concurrency = optimal
* High concurrency = saturation

---

## 10.2 Why Performance Improves

### Baseline

Each request triggers full model execution

### Batching

Multiple requests share a forward pass

### Caching

Repeated requests bypass model entirely

---

## 11. Reproducibility

This repository is fully reproducible:

### Step 1: Install

pip install -r requirements.txt

### Step 2: Configure

cp .env.example .env

### Step 3: Run server

uvicorn src.server --host 127.0.0.1 --port 8000

### Step 4: Run benchmarks

python -m benchmarks.run_benchmarks

### Step 5: Generate charts

python analysis/visualizations/generate_charts.py

---

### Benchmark Guarantees

* Warm-up excluded
* Fixed request counts
* Controlled concurrency
* Cold vs warm cache separated
* Deterministic caching

Results stored in:
benchmarks/results/results.json

---

## 11.2 Resource Usage Note

* CPU-based mock LLM used
* No GPU required
* Memory bounded by cache size
* Ensures reproducibility across environments

---

## 12. Governance Considerations

### Implemented

* SHA-256 hashed cache keys (no PII)
* TTL expiration
* Bounded cache size
* Deterministic-only caching

### Risks

* Cached responses may contain sensitive content
* No rate limiting / auth

### Future improvements

* Rate limiting
* Authentication
* Cache invalidation APIs
* Input/output moderation

---

## 13. Limitations

* Performance depends on workload
* Cache depends on repetition
* Saturation at high concurrency
* No distributed scaling

---

## 14. Conclusion

* Batching improves throughput (~25×)
* Caching reduces latency (~15×)
* System shows realistic scaling behavior

LLM systems must balance latency, throughput, and cache effectiveness.
