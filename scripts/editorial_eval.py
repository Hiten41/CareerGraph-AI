"""Editorial target retrieval on a mixed index. Unjudged background jobs are not labeled negatives."""

import json
from pathlib import Path
from statistics import mean, median, quantiles
from time import perf_counter
from uuid import uuid4
from sqlalchemy import text
from app.db.session import Session
from app.schemas.domain import Search
from app.retrieval.search import search
from app.evaluation.metrics import metrics


def evaluate():
    judgments = Path("scripts/fixtures/judgments.tsv").read_text(encoding="utf8").splitlines()
    measured = {}
    with Session.begin() as db:
        size = db.scalar(text("select count(*) from jobs"))
        if db.scalar(text("select count(*) from jobs where source='editorial-v1'")) != 12 or size < 1012:
            raise RuntimeError("Run scripts/scale_seed.py first")
        for strategy in ("keyword", "semantic", "hybrid", "personalized"):
            per_query = []
            timings = []
            for row in judgments:
                query, targets = row.split("\t")
                start = perf_counter()
                found = search(
                    db,
                    Search(query=query, strategy=strategy),
                    {"skills": ["Python", "SQL"]},
                    ["retrieval"],
                    str(uuid4()),
                )
                timings.append(1000 * (perf_counter() - start))
                ids = [r["job"]["external_id"] for r in found]
                per_query.append(
                    dict(
                        query=query,
                        targets=targets,
                        returned=ids,
                        metrics=metrics(ids, set(targets.split(","))),
                    )
                )
            averages = {k: mean(q["metrics"][k] for q in per_query) for k in per_query[0]["metrics"]}
            averages.update(p50_ms=median(timings), p95_ms=quantiles(timings, n=20, method="inclusive")[18])
            metadata = dict(
                dataset="editorial-targets-v1",
                index_size=size,
                strategy=strategy,
                queries=len(judgments),
                ranking="cosine-rrf-bounded-v2",
                embedding="all-MiniLM-L6-v2",
            )
            db.execute(
                text(
                    "INSERT INTO evaluation_runs(id,metadata,metrics) VALUES(:i,CAST(:m AS jsonb),CAST(:v AS jsonb))"
                ),
                dict(i=uuid4(), m=json.dumps(metadata), v=json.dumps(averages)),
            )
            measured[strategy] = dict(metadata=metadata, metrics=averages, queries=per_query)
    Path("docs/editorial-results.json").write_text(json.dumps(measured, indent=2))


if __name__ == "__main__":
    evaluate()
