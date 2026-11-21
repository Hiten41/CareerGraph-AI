"""Run on a fresh database seeded with exactly the default 40 fictional jobs."""

import json
from statistics import mean, median, quantiles
from time import perf_counter
from uuid import uuid4
from sqlalchemy import text
from app.db.session import Session
from app.core.config import settings
from app.schemas.domain import Search
from app.retrieval.search import search
from app.evaluation.metrics import metrics

QUERIES = [
    ["RAG", "document similarity retrieval", "evaluate nearest neighbor recall"],
    ["LangChain", "tools for a conversational assistant", "agent memory engineering"],
    ["FastAPI PostgreSQL", "relational API development", "optimize database queries"],
    ["React CSS", "accessible web components", "responsive interface implementation"],
    ["Kubernetes", "container orchestration", "trace production outages"],
    ["Spark", "event stream processing", "batch transformation pipelines"],
    ["PyTorch", "train neural classifiers", "monitor predictive model drift"],
    ["Android", "offline mobile applications", "native Kotlin engineering"],
    ["Tableau", "customer retention cohorts", "product experimentation"],
    ["Redis Go", "low latency inverted indexes", "product search infrastructure"],
]
with Session.begin() as db:
    n = db.execute(text("SELECT count(*) FROM jobs WHERE source='fictional-v1'")).scalar()
    if n != 40 or db.execute(text("SELECT count(*) FROM jobs")).scalar() != 40:
        raise SystemExit("Use isolated default seed of 40 records")
    for strategy in ("keyword", "semantic", "hybrid", "personalized"):
        scores = []
        elapsed = []
        for i, group in enumerate(QUERIES):
            relevant = {f"cg-{j:04}" for j in range(i, 40, 10) if j != 39}
            for q in group:
                start = perf_counter()
                rows = search(
                    db,
                    Search(query=q, strategy=strategy),
                    {"skills": ["Python", "SQL"]},
                    ["retrieval"],
                    str(uuid4()),
                )
                elapsed.append((perf_counter() - start) * 1000)
                scores.append(metrics([r["job"]["external_id"] for r in rows], relevant))
        values = {k: mean(s[k] for s in scores) for k in scores[0]}
        values.update(
            latency_p50_ms=median(elapsed),
            latency_p95_ms=quantiles(elapsed, n=20, method="inclusive")[18],
            llm_quality="not evaluated",
        )
        metadata = {
            "strategy": strategy,
            "dataset": "fictional-v1/40",
            "queries": 30,
            "embedding": settings.embedding_model,
            "rrf_k": 60,
            "ranking_version": "cosine-rrf-bounded-v2",
        }
        db.execute(
            text(
                "INSERT INTO evaluation_runs(id,metadata,metrics) VALUES(:i,CAST(:m AS jsonb),CAST(:v AS jsonb))"
            ),
            {"i": uuid4(), "m": json.dumps(metadata), "v": json.dumps(values)},
        )
        print(strategy, values)
