import concurrent.futures
import json
import random
import time
from typing import Any

import httpx


BASE_URL = "http://127.0.0.1:8000"
API_KEY = "change-me"
TOTAL_REQUESTS = 200
CONCURRENCY = 20


def build_payload(i: int) -> dict[str, Any]:
    return {
        "profile": {
            "agent_id": f"bot_{i}",
            "role": "collector" if i % 2 == 0 else "fighter",
            "style": "balanced",
            "metadata": {},
        },
        "observe": {
            "agent_id": f"bot_{i}",
            "tick": i,
            "state": {
                "hp": random.randint(40, 100),
                "mp": random.randint(10, 60),
                "x": random.randint(0, 500),
                "y": random.randint(0, 500),
                "map_id": random.randint(1, 10),
                "target_id": None,
                "target_distance": None,
                "safe_zone": False,
                "weight_percent": random.randint(10, 90),
                "inventory": {"potion": random.randint(0, 10)},
                "is_under_attack": False,
                "can_teleport": True,
            },
        },
        "decide": {
            "agent_id": f"bot_{i}",
            "tick": i,
            "state": {
                "hp": random.randint(40, 100),
                "mp": random.randint(10, 60),
                "x": random.randint(0, 500),
                "y": random.randint(0, 500),
                "map_id": random.randint(1, 10),
                "target_id": None,
                "target_distance": None,
                "safe_zone": False,
                "weight_percent": random.randint(10, 90),
                "inventory": {"potion": random.randint(0, 10)},
                "is_under_attack": False,
                "can_teleport": True,
            },
        },
    }


def fire(i: int) -> tuple[int, float]:
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    payload = build_payload(i)
    started = time.perf_counter()
    with httpx.Client(timeout=10.0) as client:
        res = client.post(f"{BASE_URL}/api/v1/robot/sync", headers=headers, content=json.dumps(payload))
        elapsed = time.perf_counter() - started
        return res.status_code, elapsed


if __name__ == "__main__":
    latencies = []
    statuses = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [executor.submit(fire, i) for i in range(TOTAL_REQUESTS)]
        for future in concurrent.futures.as_completed(futures):
            status, elapsed = future.result()
            latencies.append(elapsed)
            statuses[status] = statuses.get(status, 0) + 1

    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)] if latencies else 0.0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0.0

    print({
        "requests": TOTAL_REQUESTS,
        "concurrency": CONCURRENCY,
        "statuses": statuses,
        "p50": round(p50, 4),
        "p95": round(p95, 4),
        "p99": round(p99, 4),
    })
