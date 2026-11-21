"""Refresh from an operator-authorized, complete local JSON snapshot in one transaction."""

import json
from pathlib import Path
from typing import Protocol
from sqlalchemy import text
from app.schemas.domain import Job
from app.ingestion.importer import ingest


class SnapshotSource(Protocol):
    def records(self) -> list[dict]: ...


class JsonSnapshot:
    def __init__(self, path: Path):
        self.path = path

    def records(self) -> list[dict]:
        if self.path.stat().st_size > 16_000_000:
            raise ValueError("Snapshot exceeds 16 MB")
        data = json.loads(self.path.read_text(encoding="utf8"))
        if not isinstance(data, list) or len(data) > 5000:
            raise ValueError("Expected up to 5000 records")
        return data


def refresh(db, source: str, adapter: SnapshotSource, expire_missing: bool = False):
    rows = [Job.model_validate(r) for r in adapter.records()]
    if any(r.source != source for r in rows):
        raise ValueError("Source identity mismatch")
    if expire_missing and not rows:
        raise ValueError("Empty authoritative snapshot rejected")
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:source))"), {"source": source})
    result = ingest(db, [r.model_dump() for r in rows])
    expired = 0
    if expire_missing:
        expired = db.execute(
            text(
                "UPDATE jobs SET status='expired',content_hash='',updated_at=now() WHERE source=:source AND status IN ('active','unknown') AND NOT(external_id=ANY(CAST(:ids AS text[])))"
            ),
            {"source": source, "ids": [r.external_id for r in rows]},
        ).rowcount
    return {**result, "expired": expired}
