import os
from uuid import uuid4
import pytest
from sqlalchemy import text
from app.db.session import Session
from app.ingestion.importer import ingest
from app.retrieval.search import search
from app.schemas.domain import Search


@pytest.mark.skipif(
    os.getenv("CG_SEEDED_TESTS") != "1", reason="requires seeded database and embedding model"
)
def test_refresh_and_expire():
    with Session() as db:
        row = dict(
            source="qa",
            external_id="refresh",
            title="Observatory intern",
            description="Telescope alignment",
            skills=["Python"],
            company="Fictional",
            url="https://example.invalid/qa",
        )
        assert ingest(db, [row])["changed"] == 1

        def snapshot():
            return db.execute(
                text("select id,embedding::text from jobs where source='qa' and external_id='refresh'")
            ).one()

        original = snapshot()
        assert ingest(db, [row])["changed"] == 0
        row["description"] = "Maintain a spectroheliograph"
        assert ingest(db, [row])["changed"] == 1
        updated = snapshot()
        assert original.id == updated.id and original[1] != updated[1]
        req = Search(query="spectroheliograph", strategy="keyword")
        assert search(db, req, {}, [], str(uuid4()))[0]["job"]["id"] == str(original.id)
        ingest(db, [{**row, "status": "expired"}])
        assert search(db, req, {}, [], str(uuid4())) == []
        db.rollback()


@pytest.mark.skipif(os.getenv("CG_INTEGRATION") != "1", reason="requires migrated database")
def test_salary_before_cap_and_pagination():
    # Insert 603 topically identical rows. Known-ineligible rows occupy the first 600 UUIDs.
    with Session() as db:
        db.execute(
            text("""INSERT INTO jobs(id,source,external_id,title,company,description,skills,optional_skills,employment,mode,salary,currency,period,experience,status,url,synthetic,content_hash)
        SELECT ('a3000000-0000-0000-0000-'||lpad(i::text,12,'0'))::uuid,'filter-qa',i::text,'quartzanchor','QA','Test fixture','[]','[]','internship','remote',
        CASE WHEN i<=600 THEN 1000 WHEN i=603 THEN NULL ELSE 51000 END,'INR','month',0,'active','https://example.invalid',true,'fixture'
        FROM generate_series(1,603) i""")
        )
        from app.schemas.domain import Constraints

        filters = Constraints(min_salary=50000, currency="INR", period="month", max_experience=0)

        def page(offset, strict=False):
            q = Search(
                query="quartzanchor",
                strategy="keyword",
                constraints=filters.model_copy(update={"verified_only": strict}),
                limit=1,
                offset=offset,
            )
            return search(db, q, {}, [], str(uuid4()))

        assert [page(i)[0]["job"]["external_id"] for i in range(3)] == ["601", "602", "603"]
        assert page(2)[0]["eligibility"] == "uncertain" and not page(2, True)
        db.rollback()


def test_snapshot_duplicates_and_source_boundary():
    from app.ingestion.sources import refresh

    class Source:
        def __init__(self, rows):
            self.rows = rows

        def records(self):
            return self.rows

    if os.getenv("CG_SEEDED_TESTS") != "1":
        pytest.skip("requires embeddings")
    with Session() as db:
        base = dict(
            source="refresh-qa",
            external_id="first",
            title="Test",
            company="QA",
            description="Example",
            url="https://example.invalid/qa",
        )
        other = {**base, "external_id": "second"}
        assert refresh(db, "refresh-qa", Source([base, other, other]))["changed"] == 2
        assert refresh(db, "refresh-qa", Source([base]), True)["expired"] == 1
        assert refresh(db, "refresh-qa", Source([base, other]))["changed"] == 1
        with pytest.raises(ValueError):
            refresh(db, "wrong", Source([base]), True)
        db.rollback()


@pytest.mark.skipif(os.getenv("CG_INTEGRATION") != "1", reason="requires seeded database")
def test_plain_language_keyword_fallback_preserves_explicit_phrase():
    with Session() as db:
        base = "spectroheliographic mechanics"
        db.execute(
            text("""INSERT INTO jobs(id,source,external_id,title,company,description,skills,optional_skills,status,url,synthetic,content_hash)
            VALUES(:id,'lexical-test','match',:title,'Fictional','Local fixture','[]','[]','active','https://example.invalid',true,'fixture')"""),
            {"id": uuid4(), "title": base},
        )

        def results(query):
            return search(db, Search(query=query, strategy="keyword"), {}, [], str(uuid4()))

        assert results("spectroheliographic unexplained phrase")[0]["job"]["title"] == base
        assert results('"spectroheliographic unexplained phrase"') == []
        assert results("spectroheliographic -mechanics") == []
        assert results("the and was") == []
        db.rollback()
