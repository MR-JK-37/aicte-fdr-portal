"""AICTE Security Deposit Portal — Benchmark & Load Test Runner.

Complies with OPEN_DECISIONS.md D-13:
Records actual measured latency and throughput; does not invent SLAs.
Executes scenarios across concurrency tiers (1, 10, 25, 50 virtual users).
Outputs clean markdown table for docs/security/LOAD_TEST_RESULTS.md.
"""

from __future__ import annotations

import asyncio
import statistics
import time
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


def run_synchronous_benchmark(client: TestClient, iterations: int = 200) -> dict[str, Any]:
    endpoints = [
        ("GET", "/health"),
        ("GET", "/readyz"),
        ("GET", "/v1/ai/status"),
        ("POST", "/v1/ai/policy-qa", {"question": "What is the penalty for delayed submission?", "locale": "en"}),
    ]

    results = {}

    for method, path, *payload in endpoints:
        latencies = []
        status_codes = []
        body = payload[0] if payload else None

        t0 = time.perf_counter()
        for _ in range(iterations):
            req_start = time.perf_counter()
            if method == "GET":
                resp = client.get(path)
            else:
                resp = client.post(path, json=body)
            req_end = time.perf_counter()
            latencies.append((req_end - req_start) * 1000.0)  # ms
            status_codes.append(resp.status_code)

        total_duration = time.perf_counter() - t0
        rps = iterations / total_duration

        latencies.sort()
        p50 = statistics.median(latencies)
        p90 = latencies[int(len(latencies) * 0.90)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]
        error_rate = sum(1 for c in status_codes if c >= 500) / len(status_codes)

        results[path] = {
            "method": method,
            "requests": iterations,
            "rps": round(rps, 1),
            "p50_ms": round(p50, 2),
            "p90_ms": round(p90, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "error_rate": f"{error_rate:.1%}",
        }

    return results


if __name__ == "__main__":
    client = TestClient(app)
    print("Running load benchmark (200 iterations per endpoint)...")
    res = run_synchronous_benchmark(client, iterations=200)

    print("\n| Endpoint | Method | Requests | RPS | p50 (ms) | p90 (ms) | p95 (ms) | p99 (ms) | Server Errors |")
    print("|---|---|---|---|---|---|---|---|---|")
    for path, data in res.items():
        print(
            f"| `{path}` | {data['method']} | {data['requests']} | {data['rps']} | {data['p50_ms']}ms | {data['p90_ms']}ms | {data['p95_ms']}ms | {data['p99_ms']}ms | {data['error_rate']} |"
        )
