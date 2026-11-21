"""Executable agent probes on disposable database state. Counts cover these probes only."""

import json
from pathlib import Path
from uuid import uuid4
from sqlalchemy import text
from app.db.session import Session
from app.agents.orchestrator import respond
from app.repositories.user_data import job


def run():
    checks = {}
    claims = []
    uid = uuid4()
    sid = uuid4()
    with Session.begin() as db:
        db.execute(
            text("INSERT INTO users(id,email,password_hash) VALUES(:u,:e,'disabled')"),
            {"u": uid, "e": str(uid) + "@example.invalid"},
        )
        db.execute(text("INSERT INTO search_sessions(id,user_id) VALUES(:s,:u)"), {"s": sid, "u": uid})
        state = dict(id=sid, query="", constraints={}, last_jobs=[])
        prompts = [
            ("Find remote Python internships for 2028 graduates", "search_jobs"),
            ("Only AI/ML ones", "apply_job_filters"),
            ("At least 50,000 INR per month", "search_jobs"),
            ("Explain the best match", "explain_job_match"),
            ("Compare the top two jobs", "compare_jobs"),
            ("Remember that I prefer retrieval", "propose_preference_update"),
            ("confirm", "save_user_preferences"),
        ]
        retained = []
        for i, (prompt, expected) in enumerate(prompts):
            state.pop("results", None)
            response = respond(db, uid, state, prompt, local_only=True)
            checks[prompt] = expected in response["tools"]
            if i in (1, 2, 3, 4):
                retained.append(
                    state["constraints"].get("mode") == "remote"
                    and state["constraints"].get("graduation_year") == 2028
                    and state["constraints"].get("domain") == "AI/ML"
                )
            for row in response["results"]:
                source = job(db, row["job"]["id"])
                claims.extend(
                    source is not None and source[k] == row["job"][k]
                    for k in ("title", "company", "salary", "url")
                )
        metrics = dict(
            tool_selection=sum(checks.values()) / len(checks),
            retention=sum(retained) / len(retained),
            unsupported_record_fields=sum(not x for x in claims) / len(claims) if claims else None,
            record_fields_checked=len(claims),
            hosted_generation="not evaluated",
        )
        meta = dict(
            dataset="agent-script-v1",
            mode="deterministic",
            turns=len(prompts),
            retention_probes=len(retained),
        )
        db.execute(text("DELETE FROM users WHERE id=:u"), {"u": uid})
        db.execute(
            text(
                "INSERT INTO evaluation_runs(id,metadata,metrics) VALUES(:i,CAST(:m AS jsonb),CAST(:v AS jsonb))"
            ),
            {"i": uuid4(), "m": json.dumps(meta), "v": json.dumps(metrics)},
        )
        Path("docs/agent-results.json").write_text(
            json.dumps(dict(metadata=meta, metrics=metrics, checks=checks), indent=2)
        )


if __name__ == "__main__":
    run()
