import json
import re
from sqlalchemy import text
from app.schemas.domain import Search
from app.services.embeddings import embed_query
from app.retrieval.fusion import rrf
from app.retrieval.eligibility import eligibility
from app.ranking.scoring import explain


def search(db, request: Search, profile: dict, preferences: list[str], user_id: str):
    params = {"q": request.query, "cap": 600}
    # Structured filtering BEFORE bounded retrieval preserves recall for explicit constraints.
    filters = ["status NOT IN ('expired','archived')"]
    c = request.constraints
    for field in ("employment", "mode", "location", "graduation_year", "domain"):
        if getattr(c, field) is not None:
            filters.append(f"({field} IS NULL OR lower({field}::text)=lower(CAST(:{field} AS text)))")
            params[field] = getattr(c, field)
    for field in ("mode", "employment"):
        excluded = getattr(c, f"exclude_{field}")
        if excluded:
            key = f"exclude_{field}"
            params[key] = excluded
            predicate = f"NOT (lower({field}) = ANY(CAST(:{key} AS text[])))"
            filters.append(predicate if c.verified_only else f"({field} IS NULL OR {predicate})")
    if c.max_experience is not None:
        filters.append("(experience IS NULL OR experience <= :experience)")
        params["experience"] = c.max_experience
    if c.min_salary is not None and c.currency and c.period:
        filters.append(
            "(salary IS NULL OR currency IS DISTINCT FROM :currency OR period IS DISTINCT FROM :period OR salary >= :minimum)"
        )
        params.update(currency=c.currency, period=c.period, minimum=c.min_salary)
    if c.verified_only:
        filters.append("status='active'")
        for field in ("employment", "mode", "location", "graduation_year", "domain"):
            if getattr(c, field) is not None:
                filters.append(f"{field} IS NOT NULL")
        if c.max_experience is not None:
            filters.append("experience IS NOT NULL")
        if c.min_salary is not None:
            if not (c.currency and c.period):
                return []
            filters.append("salary >= :minimum AND currency=:currency AND period=:period")
    where = " AND ".join(filters)
    rankings = []
    cosine = {}
    if request.strategy != "semantic":
        rows = db.execute(
            text(
                f"SELECT id FROM jobs WHERE {where} AND search_vector @@ websearch_to_tsquery('english', :q) ORDER BY ts_rank_cd(search_vector, websearch_to_tsquery('english', :q)) DESC, id LIMIT :cap"
            ),
            params,
        )
        keyword_ids = [str(row.id) for row in rows]
        # Preserve explicit phrases, negation and boolean syntax.
        if (
            request.strategy == "keyword"
            and not keyword_ids
            and not re.search(r'["-]|\bOR\b', request.query, re.IGNORECASE)
        ):
            rows = db.execute(
                text(
                    f"""WITH relaxed AS (
                        SELECT CAST(string_agg(quote_literal(lexeme), ' | ') AS tsquery) AS query
                        FROM unnest(tsvector_to_array(to_tsvector('english', :q))) AS term(lexeme)
                    )
                    SELECT id FROM jobs CROSS JOIN relaxed
                    WHERE {where} AND search_vector @@ relaxed.query
                    ORDER BY ts_rank(search_vector, relaxed.query, 32) DESC, id LIMIT :cap"""
                ),
                params,
            )
            keyword_ids = [str(row.id) for row in rows]
        rankings.append(keyword_ids)
    if request.strategy != "keyword":
        params["vector"] = json.dumps(embed_query(request.query))
        rows = db.execute(
            text(
                f"SELECT id, 1 - (embedding <=> CAST(:vector AS vector)) AS similarity FROM jobs WHERE {where} AND embedding IS NOT NULL ORDER BY embedding <=> CAST(:vector AS vector), id LIMIT :cap"
            ),
            params,
        )
        cosine = {str(r.id): float(r.similarity) for r in rows}
        rankings.append(list(cosine))
    fused = rrf(rankings)
    if not fused:
        return []
    rows = db.execute(
        text(
            "SELECT id,source,external_id,title,company,description,skills,optional_skills,employment,mode,location,graduation_year,salary,currency,period,experience,domain,status,url,synthetic,last_seen_at FROM jobs WHERE id = ANY(CAST(:ids AS uuid[]))"
        ),
        {"ids": list(fused)},
    ).mappings()
    feedback = dict(
        db.execute(
            text("SELECT job_id, value FROM job_feedback WHERE user_id=CAST(:u AS uuid)"), {"u": user_id}
        ).all()
    )
    results = []
    for row in rows:
        job = dict(row)
        for key in ("embedding", "search_vector", "content_hash"):
            job.pop(key, None)
        job["id"] = str(job["id"])
        status, unknown = eligibility(job, c)
        if status == "ineligible":
            continue
        explanation = explain(
            job,
            profile,
            fused[job["id"]],
            preferences if request.strategy == "personalized" else [],
            feedback.get(row["id"], 0) if request.strategy == "personalized" else 0,
            similarity=cosine.get(job["id"], 0),
        )
        if request.strategy != "personalized":
            explanation["score"] = fused[job["id"]]
        results.append({"job": job, "eligibility": status, "unknown": unknown, "explanation": explanation})
    results.sort(key=lambda r: (-r["explanation"]["score"], r["job"]["id"]))
    return results[request.offset : request.offset + request.limit]
