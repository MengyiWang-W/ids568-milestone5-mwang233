Performance Report: Batching and Caching in LLM Serving
1. Objective

The objective of this project is to evaluate how dynamic batching and response caching impact the performance of a FastAPI-based LLM inference service.

This report focuses on:

Comparing baseline vs optimized system performance
Evaluating behavior under different concurrency levels
Measuring cache effectiveness
Analyzing latency–throughput trade-offs
Identifying scalability limits and system bottlenecks
2. System Design
2.1 Baseline System
Endpoint: /generate_baseline
Each request is processed independently
No batching
No caching

This represents a naïve, sequential inference pipeline.

2.2 Optimized System
Endpoint: /generate

Processing pipeline:

Cache lookup
Cache miss → enqueue request
Dynamic batching execution
Cache write-back

Features:

Dynamic batching (queue + timeout)
LRU cache with TTL

This represents a production-style LLM serving system.

3. Methodology
3.1 Workload
Total requests: 50
Temperature: 0.0 (deterministic → cacheable)
Prompt distribution: mix of repeated and unique prompts
3.2 Concurrency Levels
Level	Concurrency
Low	10
Medium	50
High	100
3.3 Metrics Collected
Average latency (ms)
P50 latency (ms)
P95 latency (ms)
Throughput (req/s)
Cache hit rate
4. Results
4.1 Baseline
Metric	Value
Avg latency	94.71 ms
P50 latency	97.34 ms
P95 latency	108.25 ms
Throughput	10.56 req/s
Cache hit	0.0
4.2 Optimized — Low Concurrency
Metric	Value
Avg latency	36.92 ms
P50 latency	13.21 ms
P95 latency	254.34 ms
Throughput	131.19 req/s
Cache hit	0.9
Comparison vs Baseline
Throughput: 10.56 → 131.19 (~12× increase)
Latency: 94.71 → 36.92 (~61% reduction)
4.3 Optimized — Medium Concurrency
Metric	Value
Avg latency	34.54 ms
P50 latency	28.55 ms
P95 latency	67.3 ms
Throughput	263.97 req/s
Cache hit	1.0
Comparison vs Low
Throughput: 131.19 → 263.97 (~2× increase)
Latency: 36.92 → 34.54 (slight improvement)
4.4 Optimized — High Concurrency
Metric	Value
Avg latency	59.55 ms
P50 latency	49.39 ms
P95 latency	114.81 ms
Throughput	262.5 req/s
Cache hit	1.0
Comparison vs Medium
Throughput: 263.97 → 262.5 (plateau)
Latency: 34.54 → 59.55 (increase)
4.5 Cache Performance
Metric	Value
Cold latency	203.62 ms
Warm latency	13.25 ms
Speedup	15.37×
Cold hit rate	0.0
Warm hit rate	1.0
5. Analysis
5.1 Effect of Batching

Batching significantly improves throughput:

Baseline: 10.56 req/s
Medium load: 263.97 req/s (~25× increase)

At low and medium concurrency, batching also reduces average latency due to more efficient model execution.

However, batching introduces queue delay:

P95 latency at low concurrency reaches 254 ms
Latency increases at high concurrency

Key insight:

Dynamic batching improves throughput by amortizing model execution cost, but introduces queueing delay that increases latency under higher load.

5.2 Effect of Caching

Caching eliminates redundant computation:

Cold latency: 203.62 ms
Warm latency: 13.25 ms
Speedup: ~15×

Key insight:

Cached responses bypass model inference, resulting in substantial latency reduction.

5.3 Cache Hit Behavior
Cold phase: hit rate = 0.0
Warm phase: hit rate = 1.0

Interpretation:

Cache effectiveness depends entirely on input repetition. When prompts are reused, caching provides maximum benefit.

5.4 Latency Distribution (Tail Behavior)

P95 latency behavior:

Low: 254 ms
Medium: 67 ms
High: 114 ms

Key insight:

Tail latency is influenced by batching queue delays, especially when requests wait longer to form batches. This effect is more visible at low concurrency.

5.5 System Saturation

Throughput behavior:

Low: 131 req/s
Medium: 264 req/s
High: 262 req/s

Interpretation:

Throughput plateaus at high concurrency, indicating system saturation where additional load no longer improves performance.

6. Trade-off Analysis
6.1 Latency vs Throughput Trade-off
Load	Latency	Throughput
Low	Low	High
Medium	Low	Highest
High	Moderate	Plateau

Conclusion:

The system achieves optimal performance at medium concurrency, where throughput is maximized while latency remains controlled.

6.2 Batching Trade-off
Larger batches → higher throughput
Larger batches → increased waiting time
6.3 Cache Trade-off
High hit rate → significant latency reduction
Low hit rate → minimal benefit
7. Hidden Pitfalls (Critical Section)

Batching Queue Delay

Even at low concurrency, some requests experience high latency (P95 = 254 ms) due to waiting for batch formation.

Non-linear Scaling

Throughput does not increase indefinitely with concurrency. It plateaus at high load due to system capacity limits.

Latency Increase at High Load

At high concurrency, latency increases due to queueing, even though throughput no longer improves.

Cache Dependence on Workload

Cache effectiveness is highly dependent on prompt repetition and may not generalize to highly diverse workloads.

8. Improvement Strategies
Adaptive batching (dynamic timeout tuning)
Reducing queue waiting time under high load
Cache-aware request grouping
Improved cache eviction strategies
Load control / backpressure mechanisms
9. Conclusion

This project demonstrates:

Dynamic batching significantly improves throughput (~25× increase)
Caching drastically reduces latency (~15× speedup)
The system exhibits non-linear scaling and saturation behavior

Most importantly:

LLM serving systems involve inherent trade-offs between latency, throughput, and cache effectiveness. Optimal performance requires careful tuning based on workload characteristics and system capacity limits.