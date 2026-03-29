import json
import os
import matplotlib.pyplot as plt

RESULTS_PATH = "benchmarks/results/results.json"
OUTPUT_DIR = "analysis/visualizations"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================
# Helper Functions
# ==============================
def safe_get(data, path, default=0):
    try:
        for p in path:
            data = data[p]
        return data
    except:
        return default

def add_labels(ax, values):
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8)

def save_bar_chart(title, labels, values, ylabel, filename):
    plt.figure()
    ax = plt.gca()
    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    add_labels(ax, values)

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/{filename}")
    plt.close()

# ==============================
# Load Data
# ==============================
if not os.path.exists(RESULTS_PATH):
    raise FileNotFoundError(f"{RESULTS_PATH} not found")

with open(RESULTS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)


labels = ["Baseline", "Low", "Medium", "High"]


# ==============================
# 1. Throughput
# ==============================
throughput = [
    safe_get(data, ["baseline", "throughput_req_per_s"]),
    safe_get(data, ["low", "throughput_req_per_s"]),
    safe_get(data, ["medium", "throughput_req_per_s"]),
    safe_get(data, ["high", "throughput_req_per_s"]),
]

save_bar_chart(
    "Throughput Comparison",
    labels,
    throughput,
    "Requests/sec",
    "throughput.png",
)


# ==============================
# 2. Average Latency
# ==============================
latency = [
    safe_get(data, ["baseline", "avg_latency_ms"]),
    safe_get(data, ["low", "avg_latency_ms"]),
    safe_get(data, ["medium", "avg_latency_ms"]),
    safe_get(data, ["high", "avg_latency_ms"]),
]

save_bar_chart(
    "Average Latency",
    labels,
    latency,
    "Latency (ms)",
    "latency_avg.png",
)


# ==============================
# 3. P95 Latency（关键加分）
# ==============================
p95 = [
    safe_get(data, ["baseline", "p95_latency_ms"]),
    safe_get(data, ["low", "p95_latency_ms"]),
    safe_get(data, ["medium", "p95_latency_ms"]),
    safe_get(data, ["high", "p95_latency_ms"]),
]

save_bar_chart(
    "P95 Latency",
    labels,
    p95,
    "Latency (ms)",
    "latency_p95.png",
)


# ==============================
# 4. Cache Hit Rate
# ==============================
hit_rate = [
    safe_get(data, ["baseline", "cache_hit_rate"]),
    safe_get(data, ["low", "cache_hit_rate"]),
    safe_get(data, ["medium", "cache_hit_rate"]),
    safe_get(data, ["high", "cache_hit_rate"]),
]

plt.figure()
plt.plot(labels, hit_rate, marker="o")
plt.title("Cache Hit Rate by Load")
plt.ylabel("Hit Rate")
plt.ylim(0, 1.05)
plt.grid(True, linestyle="--", alpha=0.5)

for i, v in enumerate(hit_rate):
    plt.text(i, v, f"{v:.2f}", ha="center")

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/cache_hit_rate.png")
plt.close()


# ==============================
# 5. Cold vs Warm Cache
# ==============================
cold = safe_get(data, ["cache", "cold_avg_ms"])
warm = safe_get(data, ["cache", "warm_avg_ms"])

save_bar_chart(
    "Cold vs Warm Cache Latency",
    ["Cold", "Warm"],
    [cold, warm],
    "Latency (ms)",
    "cold_vs_warm.png",
)


# ==============================
# 6. Warm Cache Hit Rate Over Time
# ==============================
series = safe_get(data, ["cache", "warm_hit_rate_over_time"], [])

if series:
    plt.figure()
    plt.plot(range(len(series)), series)
    plt.title("Warm Cache Hit Rate Over Time")
    plt.xlabel("Request Index")
    plt.ylabel("Hit Rate")
    plt.ylim(0, 1.05)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/hit_rate_over_time.png")
    plt.close()


# ==============================
# 7. Latency Over Time
# ==============================
lat_series = safe_get(data, ["cache", "warm_latency_sequence_ms"], [])

if lat_series:
    plt.figure()
    plt.plot(range(len(lat_series)), lat_series)
    plt.title("Latency Over Time (Warm Cache)")
    plt.xlabel("Request Index")
    plt.ylabel("Latency (ms)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/latency_over_time.png")
    plt.close()


# ==============================
# 8. TTL Behavior（加分点）
# ==============================
ttl = data.get("ttl_expiration_test", {})

if not ttl.get("skipped", True):
    observed = ttl.get("observed_pattern", [])

    values = [1 if x else 0 for x in observed]

    save_bar_chart(
        "TTL Expiration Behavior",
        ["Req1", "Req2", "Req3"],
        values,
        "Hit (1) / Miss (0)",
        "ttl_behavior.png",
    )


# ==============================
# 9. Resource Usage
# ==============================
def extract(key, metric):
    return safe_get(data, [key, "local_system_after", metric])


cpu = [extract(k, "runner_cpu_percent") for k in ["baseline", "low", "medium", "high"]]
mem = [extract(k, "runner_memory_rss_mb") for k in ["baseline", "low", "medium", "high"]]

save_bar_chart("CPU Usage", labels, cpu, "CPU %", "cpu.png")
save_bar_chart("Memory Usage", labels, mem, "Memory MB", "memory.png")


print("✅ All charts saved to analysis/visualizations/")