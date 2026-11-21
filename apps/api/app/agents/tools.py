from typing import Any
from typing import Literal
from uuid import UUID
from pydantic import Field
from sqlalchemy import text
from app.schemas.domain import Strict, Search, Constraints
from app.repositories import user_data
from app.retrieval.search import search
from app.ranking.scoring import explain


class Empty(Strict):
    pass


class Filters(Strict):
    constraints: Constraints


class Identifier(Strict):
    job_id: UUID


class Compare(Strict):
    job_ids: list[UUID] = Field(min_length=2, max_length=2)


class Preference(Strict):
    preference: str = Field(min_length=1, max_length=300)


class Feedback(Identifier):
    value: Literal[-1, 1]


SCHEMAS: dict[str, type[Strict]] = {
    "get_candidate_profile": Empty,
    "search_jobs": Search,
    "apply_job_filters": Filters,
    "retrieve_job_details": Identifier,
    "explain_job_match": Identifier,
    "compare_jobs": Compare,
    "get_saved_jobs": Empty,
    "get_user_preferences": Empty,
    "propose_preference_update": Preference,
    "save_user_preferences": Empty,
    "record_job_feedback": Feedback,
}


def dispatch(name, arguments, db, uid, state, authorized=False):
    args: Any = SCHEMAS[name].model_validate(arguments)
    if name == "get_candidate_profile":
        return user_data.profile(db, uid)
    if name == "get_user_preferences":
        return user_data.preferences(db, uid)
    if name == "search_jobs":
        merged = {**state["constraints"], **args.constraints.model_dump(exclude_unset=True)}
        args.constraints = Constraints.model_validate(merged)
        state["constraints"] = merged
        state["query"] = args.query
        result = search(db, args, user_data.profile(db, uid), user_data.preferences(db, uid), str(uid))
        state["last_jobs"] = [r["job"]["id"] for r in result]
        state["results"] = result
        return result
    if name == "apply_job_filters":
        merged = {**state["constraints"], **args.constraints.model_dump(exclude_unset=True)}
        Constraints.model_validate(merged)
        state["constraints"] = merged
        return merged
    if name in ("retrieve_job_details", "explain_job_match"):
        job = user_data.job(db, args.job_id)
        if not job:
            raise ValueError("Job not found")
        return (
            job
            if name == "retrieve_job_details"
            else {
                "job": job,
                "explanation": explain(job, user_data.profile(db, uid), 0, user_data.preferences(db, uid)),
            }
        )
    if name == "compare_jobs":
        return [dispatch("explain_job_match", {"job_id": str(j)}, db, uid, state) for j in args.job_ids]
    if name == "get_saved_jobs":
        return [
            user_data.job(db, j)
            for j in db.execute(text("SELECT job_id FROM saved_jobs WHERE user_id=:u"), {"u": uid}).scalars()
        ]
    if name == "propose_preference_update":
        state["pending_preference"] = args.preference
        return {"confirmation_required": True, "proposed": args.preference}
    if name == "save_user_preferences":
        if not authorized or not state.get("pending_preference"):
            raise ValueError("Explicit confirmation required")
        db.execute(
            text(
                "INSERT INTO candidate_preferences(user_id,preference) VALUES(:u,:p) ON CONFLICT DO NOTHING"
            ),
            {"u": uid, "p": state["pending_preference"]},
        )
        state["pending_preference"] = None
        return {"saved": True}
    if name == "record_job_feedback":
        if not authorized:
            raise ValueError("Use the explicit feedback control")
        db.execute(
            text(
                "INSERT INTO job_feedback(user_id,job_id,value) VALUES(:u,:j,:v) ON CONFLICT(user_id,job_id) DO UPDATE SET value=EXCLUDED.value"
            ),
            {"u": uid, "j": args.job_id, "v": args.value},
        )
        return {"recorded": True}
    raise ValueError("Unknown tool")
