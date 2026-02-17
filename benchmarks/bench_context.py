from __future__ import annotations

import random
import time
import tracemalloc
from pathlib import Path

from lcm.engine import LCMEngine


def make_msg(i: int) -> tuple[str, str]:
    role = "user" if i % 2 else "assistant"
    tok = random.randint(60, 180)
    words = [f"m{i}", "context", "memory", "compression", "dag", "token", "budget"] * (tok // 7 + 1)
    return role, " ".join(words[:tok])


def run_case(n: int, root: Path) -> dict:
    engine = LCMEngine(root / f"store_{n}.jsonl", tau_soft=4000, tau_hard=6000)
    add_latencies = []

    tracemalloc.start()
    t0 = time.perf_counter()
    for i in range(1, n + 1):
        role, content = make_msg(i)
        s = time.perf_counter()
        engine.receive(role, content)
        add_latencies.append((time.perf_counter() - s) * 1000)
    total_ms = (time.perf_counter() - t0) * 1000
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    active = engine.context.get_active_context()
    depth = max((node.level for node in engine.dag.nodes.values()), default=0)
    compress_calls = sum(engine.compactor.compress_stats.values())
    compress_time_ms = total_ms - sum(add_latencies)

    return {
        "messages": n,
        "add_latency_ms_avg": round(sum(add_latencies) / len(add_latencies), 3),
        "add_latency_ms_p95": round(sorted(add_latencies)[int(len(add_latencies) * 0.95) - 1], 3),
        "compress_time_ms_est": round(max(0.0, compress_time_ms), 3),
        "compress_calls": compress_calls,
        "memory_current_mb": round(current / 1024 / 1024, 3),
        "memory_peak_mb": round(peak / 1024 / 1024, 3),
        "dag_nodes": len(engine.dag.nodes),
        "dag_depth": depth,
        "active_tokens": active["token_estimate"],
    }


def main() -> None:
    random.seed(42)
    root = Path(".bench_data")
    root.mkdir(exist_ok=True)

    for n in (100, 500, 1000):
        print(run_case(n, root))


if __name__ == "__main__":
    main()
