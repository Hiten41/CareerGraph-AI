import hashlib
import json
from uuid import uuid4
from sqlalchemy import text
from app.schemas.domain import Job
from app.services.embeddings import embed_batch


def ingest(db, records: list[dict]):
    validated = [Job.model_validate(r) for r in records]
    changed = []
    unique = {(job.source, job.external_id): job for job in validated}
    for job in unique.values():
        data = job.model_dump()
        digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        old = db.execute(
            text("SELECT content_hash FROM jobs WHERE source=:source AND external_id=:external_id"), data
        ).scalar()
        if old == digest:
            db.execute(
                text("UPDATE jobs SET last_seen_at=now() WHERE source=:source AND external_id=:external_id"),
                data,
            )
            continue
        changed.append((data, digest))
    for start in range(0, len(changed), 32):
        batch = changed[start : start + 32]
        vectors = embed_batch(
            [d["title"] + " " + " ".join(d["skills"]) + " " + d["description"] for d, _ in batch]
        )
        for (data, digest), vector in zip(batch, vectors, strict=True):
            data.update(id=str(uuid4()), content_hash=digest, embedding=json.dumps(vector))
            for field in ("skills", "optional_skills"):
                data[field] = json.dumps(data[field])
            columns = list(data)
            values = [
                f"CAST(:{k} AS jsonb)"
                if k in ("skills", "optional_skills")
                else (f"CAST(:{k} AS vector)" if k == "embedding" else f":{k}")
                for k in columns
            ]
            updates = ",".join(
                f"{k}=EXCLUDED.{k}" for k in columns if k not in ("id", "source", "external_id")
            )
            db.execute(
                text(
                    f"INSERT INTO jobs ({','.join(columns)}) VALUES ({','.join(values)}) ON CONFLICT(source,external_id) DO UPDATE SET {updates}, updated_at=now(), last_seen_at=now()"
                ),
                data,
            )
    db.execute(
        text("INSERT INTO ingestion_runs(id,count) VALUES(:id,:count)"),
        {"id": str(uuid4()), "count": len(changed)},
    )
    return {"received": len(validated), "changed": len(changed)}
