"""Measure authenticated HTTP latency with four concurrent clients against a local demo."""

import argparse
import json
import platform
from concurrent.futures import ThreadPoolExecutor
from statistics import median, quantiles
from time import perf_counter
from uuid import uuid4
from urllib.parse import urlparse
from pathlib import Path
import httpx


def benchmark(base, n):
    if urlparse(base).hostname not in ("localhost", "127.0.0.1"):
        raise ValueError("Local benchmark only")
    url = base + "/api/v1"
    with httpx.Client(timeout=60) as client:
        res = client.post(
            url + "/auth/register",
            json={"email": f"bench-{uuid4()}@example.invalid", "password": str(uuid4())},
        )
        res.raise_for_status()
        client.headers["x-csrf-token"] = res.json()["csrf"]
        queries = ["river gauge forecasting", "live subtitles", "point in time recovery", "parcel geometry"]

        def send(i):
            start = perf_counter()
            try:
                r = client.post(url + "/jobs/search", json={"query": queries[i % 4]})
                return (perf_counter() - start) * 1000, r.status_code
            except httpx.HTTPError:
                return (perf_counter() - start) * 1000, 0

        try:
            for i in range(4):
                assert send(i)[1] == 200
            start = perf_counter()
            with ThreadPoolExecutor(max_workers=4) as pool:
                samples = list(pool.map(send, range(n)))
            elapsed = perf_counter() - start
            lat = [ms for ms, code in samples if code == 200]
            report = dict(
                requests=n,
                concurrency=4,
                success=len(lat),
                error_rate=1 - len(lat) / n,
                elapsed_seconds=elapsed,
                success_per_second=len(lat) / elapsed,
                p50_ms=median(lat),
                p95_ms=quantiles(lat, n=20, method="inclusive")[18],
                machine=platform.processor(),
                system=platform.platform(),
                query_cache="four warm queries",
                database="see deployment-specific pool settings",
            )
            print(json.dumps(report, indent=2))
            Path("docs/http-load.json").write_text(json.dumps(report, indent=2))
        finally:
            client.delete(url + "/auth/me").raise_for_status()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--count", type=int, default=40)
    args = parser.parse_args()
    benchmark(args.base, args.count)
