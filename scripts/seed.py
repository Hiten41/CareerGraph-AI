"""Auditable fictional inventory and independent query wording for evaluation."""

import argparse
import csv
import json
from pathlib import Path
from uuid import uuid4
from sqlalchemy import text
from app.db.session import Session
from app.ingestion.importer import ingest
from app.auth.security import hasher
from app.repositories.user_data import save_profile
import os

CATALOG = [
    (
        "Retrieval Engineering",
        "Python SQL RAG",
        "Build a document index and evaluate nearest-neighbor recall.",
        "AI/ML",
    ),
    (
        "Agent Engineering",
        "Python LangChain FastAPI",
        "Implement tool selection and conversational memory.",
        "AI/ML",
    ),
    (
        "Backend Engineering",
        "Python PostgreSQL FastAPI",
        "Design relational APIs and optimize database queries.",
        "Backend",
    ),
    (
        "Frontend Engineering",
        "React TypeScript CSS",
        "Build accessible interfaces and responsive design systems.",
        "Frontend",
    ),
    (
        "Platform Reliability",
        "Docker Linux Kubernetes",
        "Operate containers and trace service outages.",
        "Infrastructure",
    ),
    ("Data Engineering", "SQL Python Spark", "Clean event streams and build batch pipelines.", "Data"),
    (
        "Machine Learning",
        "PyTorch Python NumPy",
        "Train neural networks and monitor classifier drift.",
        "AI/ML",
    ),
    (
        "Mobile Engineering",
        "Kotlin Android Java",
        "Ship native Android experiences and offline storage.",
        "Mobile",
    ),
    (
        "Product Analytics",
        "SQL Tableau Statistics",
        "Design experiments and interpret retention cohorts.",
        "Data",
    ),
    (
        "Search Infrastructure",
        "Go Redis PostgreSQL",
        "Serve low latency inverted indexes for product search.",
        "Backend",
    ),
]


def inventory(count=40):
    for i in range(count):
        title, skills, description, domain = CATALOG[i % 10]
        cohort = i // 10
        yield dict(
            source="fictional-v1",
            external_id=f"cg-{i:04}",
            title=title + " Intern",
            company=["Fern Circuit", "Orbit Loom", "Aster Field", "Juniper Works"][cohort % 4],
            description=description,
            skills=skills.split(),
            domain=domain,
            employment="internship",
            mode=["remote", "hybrid", "onsite", None][cohort % 4],
            location=["Bangalore", "Delhi", "Pune", None][cohort % 4],
            graduation_year=[2028, 2027, 2028, None][cohort % 4],
            experience=[0, 1, 3, None][cohort % 4],
            salary=[55000, 35000, 78000, None][cohort % 4],
            currency=["INR", "INR", "USD", None][cohort % 4],
            period=["month", "month", "year", None][cohort % 4],
            status="expired" if i == 39 else "active",
            url=f"https://example.invalid/jobs/{i}",
            synthetic=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path)
    parser.add_argument("--count", type=int, default=40)
    args = parser.parse_args()
    records = list(inventory(args.count))
    if args.file:
        if args.file.suffix.lower() == ".csv":
            with args.file.open(encoding="utf-8-sig", newline="") as f:
                records = [
                    {
                        k: (
                            [x.strip() for x in v.split("|") if x.strip()]
                            if k in ("skills", "optional_skills")
                            else v or None
                        )
                        for k, v in row.items()
                    }
                    for row in csv.DictReader(f)
                ]
        else:
            records = json.loads(args.file.read_text(encoding="utf8"))
    with Session.begin() as db:
        print(ingest(db, records))
        if password := os.getenv("DEMO_PASSWORD"):
            if len(password) < 12:
                raise ValueError("Use at least 12 characters")
            uid = db.execute(
                text(
                    "INSERT INTO users(id,email,password_hash) VALUES(:i,'demo@example.invalid',:p) ON CONFLICT DO NOTHING RETURNING id"
                ),
                {"i": uuid4(), "p": hasher.hash(password)},
            ).scalar()
            if uid:
                save_profile(
                    db,
                    uid,
                    {"name": "Demo Candidate", "skills": ["Python", "SQL", "RAG"], "graduation_year": 2028},
                )
