"""Report judged-target gains on held-out query clusters. Also retain every query for audit."""

import argparse
import json
import random
from pathlib import Path
from math import log2
from collections import defaultdict
from statistics import mean, median, quantiles
from time import perf_counter
from uuid import uuid4
from sqlalchemy import text
from app.db.session import Session
from app.schemas.domain import Search, Constraints
from app.retrieval.search import search
from app.evaluation.metrics import metrics


def cases(fusion: bool):
    if fusion:
        for line in Path("scripts/fixtures/fusion_cases.jsonl").read_text(encoding="utf8").splitlines():
            fixture = json.loads(line)
            yield fixture["query"], fixture["grades"], fixture.get("filters", {}), fixture["category"]
        return

    for line in Path("scripts/fixtures/graded.txt").read_text(encoding="utf8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        primary, secondary, condition, variants = line.split(";")
        grades = {k: 1 for k in secondary.split(",") if k != "-"} | {primary: 3}
        filters = {}
        if condition.startswith("pay"):
            filters = dict(
                min_salary=int(condition[3:]) * 1000, currency="INR", period="month", verified_only=True
            )
        elif condition != "-":
            filters = dict(mode=condition, verified_only=True)
        for query in variants.split("|"):
            yield query, grades, filters, condition


def run(fusion: bool = False):
    profiles = [({"skills": ["OpenCV", "Python"]}, ["image"]), ({"skills": ["Go", "Linux"]}, ["storage"])]
    report = {}
    with Session.begin() as db:
        for strategy in ("keyword", "semantic", "hybrid", "personalized"):
            rows = []
            groups = defaultdict(list)
            errors = 0
            total = 0
            for i, (q, g, f, category) in enumerate(cases(fusion)):
                profile, prefs = profiles[i % 2]
                start = perf_counter()
                hits = search(
                    db,
                    Search(query=q, strategy=strategy, constraints=Constraints(**f)),
                    profile,
                    prefs,
                    str(uuid4()),
                )
                ms = (perf_counter() - start) * 1000
                ids = [h["job"]["external_id"] for h in hits]
                m = metrics(ids, set(g))
                for k in (5, 10):

                    def dcg(vals):
                        return sum((2**v - 1) / log2(n + 2) for n, v in enumerate(vals[:k]))

                    m[f"ndcg_{k}"] = dcg([g.get(x, 0) for x in ids]) / dcg(sorted(g.values(), reverse=True))
                for h in hits:
                    j = h["job"]
                    total += 1
                    errors += int(
                        j["status"] in ("expired", "archived")
                        or ("mode" in f and j["mode"] != f["mode"])
                        or any(
                            key in f and (j[field] in f[key] or (f.get("verified_only") and j[field] is None))
                            for field in ("mode", "employment")
                            for key in (f"exclude_{field}",)
                        )
                        or (
                            "min_salary" in f
                            and (
                                j["currency"] != "INR"
                                or j["period"] != "month"
                                or j["salary"] is None
                                or j["salary"] < f["min_salary"]
                            )
                        )
                    )
                groups[category].append(m["ndcg_10"])
                rows.append(dict(query=q, grades=g, filters=f, profile=i % 2, ids=ids, metrics=m, ms=ms))
            avg = {k: mean(r["metrics"][k] for r in rows) for k in rows[0]["metrics"]}
            times = [r["ms"] for r in rows]
            avg.update(
                p50_ms=median(times),
                p95_ms=quantiles(times, n=20, method="inclusive")[18],
                constraint_violations=errors,
                returned=total,
                violation_rate=errors / total if total else None,
            )
            meta = dict(
                dataset="fusion-cases-v1" if fusion else "graded-targets-v1",
                sample_count=len(rows),
                intent_clusters=len(rows) if fusion else 25,
                index_size=db.scalar(text("select count(*) from jobs")),
                strategy=strategy,
                model="all-MiniLM-L6-v2",
                ranking="cosine-rrf-bounded-v2",
                rrf_k=60,
                lexical="strict-then-any-v1" if strategy == "keyword" else "strict",
            )
            db.execute(
                text(
                    "INSERT INTO evaluation_runs(id,metadata,metrics) VALUES(:id,CAST(:m AS jsonb),CAST(:v AS jsonb))"
                ),
                dict(id=uuid4(), m=json.dumps(meta), v=json.dumps(avg)),
            )
            report[strategy] = dict(
                metadata=meta, metrics=avg, by_category={k: mean(v) for k, v in groups.items()}, queries=rows
            )
    if fusion:
        pairs = list(zip(report["semantic"]["queries"], report["hybrid"]["queries"], strict=True))
        differences = [h["metrics"]["ndcg_10"] - s["metrics"]["ndcg_10"] for s, h in pairs]
        rng = random.Random(42)
        bootstrap = sorted(mean(rng.choices(differences, k=len(differences))) for _ in range(4000))
        report["paired_comparison"] = dict(
            changed_top10=sum(s["ids"] != h["ids"] for s, h in pairs),
            helped=sum(d > 0 for d in differences),
            hurt=sum(d < 0 for d in differences),
            mean_delta=mean(differences),
            descriptive_bootstrap_95=[bootstrap[100], bootstrap[3899]],
        )
    output = "docs/fusion-results.json" if fusion else "docs/graded-results.json"
    Path(output).write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fusion", action="store_true")
    run(parser.parse_args().fusion)
