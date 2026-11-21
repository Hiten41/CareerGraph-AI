"""Generate the stress inventory separately from the fixed editorial judgments."""

import json
import random
import time
from pathlib import Path
from seed import CATALOG
from app.db.session import Session
from app.ingestion.importer import ingest

SECTORS = [
    "transit schedules",
    "museum collections",
    "weather stations",
    "warehouse orders",
    "library lending",
    "classroom assignments",
    "renewable power meters",
    "agricultural sensors",
    "sports fixtures",
    "public park surveys",
]
TASKS = [
    "design a replayable importer",
    "investigate tail latency",
    "document schema changes",
    "verify accessibility",
    "monitor freshness",
    "compare retrieval quality",
    "audit missing values",
    "measure cold starts",
    "automate regression checks",
    "review statistical drift",
]


def generate():
    rng = random.Random(89341)
    for i in range(1000):
        role, skills, desc, domain = CATALOG[i % 10]
        sector = SECTORS[(i // 10) % 10]
        task = TASKS[i // 100]
        employment = rng.choice(["internship", "full-time"])
        currency, period, salary = rng.choice(
            [("INR", "month", 55000), ("USD", "year", 72000), ("EUR", "hour", 23), (None, None, None)]
        )
        yield dict(
            source="scale-v1",
            external_id=f"s{i}",
            title=f"{role} {'Intern' if employment == 'internship' else 'Engineer'}",
            company=f"Fictional Studio {i % 47}",
            description=f"{desc} Work with {sector} to {task}.",
            skills=skills.split(),
            employment=employment,
            mode=rng.choice(["remote", "hybrid", "onsite", None]),
            location=rng.choice(["Delhi", "Pune", "Bangalore", None]),
            graduation_year=rng.choice([2027, 2028, None]),
            experience=rng.choice([0, 1, 3, None]),
            domain=domain,
            currency=currency,
            period=period,
            salary=salary,
            status=rng.choices(["active", "unknown", "expired", "archived"], weights=[90, 4, 4, 2])[0],
            url=f"https://example.invalid/scale/{i}",
        )


def inventory():
    records = list(generate())
    for line in Path("scripts/fixtures/editorial.tsv").read_text(encoding="utf8").splitlines():
        key, title, description, skills, mode, salary = line.split("\t")
        records.append(
            dict(
                source="editorial-v1",
                external_id=key,
                title=title,
                description=description,
                skills=skills.split(","),
                mode=mode,
                employment="internship",
                company="Fictional Field Lab",
                salary=int(salary),
                currency="INR",
                period="month",
                url=f"https://example.invalid/editorial/{key}",
            )
        )
    return records


if __name__ == "__main__":
    rows = inventory()
    measurements = []
    for attempt in range(2):
        start = time.perf_counter()
        with Session.begin() as db:
            result = ingest(db, rows)
        measurements.append({**result, "elapsed_seconds": time.perf_counter() - start})
    print(json.dumps(measurements))
