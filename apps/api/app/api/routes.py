import json
import secrets
from uuid import UUID, uuid4
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile
from pydantic import Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from argon2.exceptions import VerificationError
from fastapi.encoders import jsonable_encoder
from app.auth.security import current_user, admin, digest, hasher
from app.db.session import database
from app.core.config import settings
from app.schemas.domain import Strict, Profile, Search, Job
from app.repositories import user_data
from app.retrieval.search import search
import httpx
from app.services.resume import parse_pdf, pdf_text, hosted_extract
from app.agents.orchestrator import respond
from app.ingestion.importer import ingest

router = APIRouter(prefix="/api/v1")


class Credentials(Strict):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254)
    password: str = Field(min_length=12, max_length=128)


class Message(Strict):
    allow_provider: bool = False
    message: str = Field(min_length=1, max_length=2000)


class Preferences(Strict):
    preferences: list[str] = Field(max_length=30)


class Feedback(Strict):
    job_id: UUID
    value: Literal[-1, 1]


class Saved(Strict):
    job_id: UUID


class Comparison(Strict):
    job_ids: list[UUID] = Field(min_length=2, max_length=2)


def login_cookie(db, response, uid):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    db.execute(
        text(
            "INSERT INTO auth_sessions(token_hash,user_id,csrf,expires_at) VALUES(:t,:u,:c,now()+interval '7 days')"
        ),
        {"t": digest(token), "u": uid, "c": csrf},
    )
    response.set_cookie(
        "cg_session",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=604800,
        path="/",
    )
    return {"csrf": csrf}


@router.post("/auth/register", status_code=201)
def register(body: Credentials, response: Response, db=Depends(database)):
    uid = uuid4()
    try:
        db.execute(
            text("INSERT INTO users(id,email,password_hash) VALUES(:i,:e,:p)"),
            {"i": uid, "e": body.email.lower(), "p": hasher.hash(body.password)},
        )
    except IntegrityError:
        raise HTTPException(409, "Email already registered") from None
    user_data.save_profile(db, uid, Profile().model_dump())
    return login_cookie(db, response, uid)


@router.post("/auth/login")
def login(body: Credentials, response: Response, db=Depends(database)):
    user = (
        db.execute(text("SELECT id,password_hash FROM users WHERE email=:e"), {"e": body.email.lower()})
        .mappings()
        .first()
    )
    try:
        valid: bool = hasher.verify(user["password_hash"] if user else DUMMY_HASH, body.password)
    except VerificationError:
        valid = False
    if not valid or not user:
        raise HTTPException(401, "Invalid email or password")
    return login_cookie(db, response, user["id"])


DUMMY_HASH = hasher.hash("not-a-real-user-password")


@router.get("/auth/me")
def me(user=Depends(current_user)):
    return user


@router.post("/auth/logout")
def logout(request: Request, response: Response, user=Depends(current_user), db=Depends(database)):
    db.execute(
        text("DELETE FROM auth_sessions WHERE token_hash=:t"),
        {"t": digest(request.cookies.get("cg_session", ""))},
    )
    response.delete_cookie("cg_session", path="/")
    return {"ok": True}


@router.delete("/auth/me")
def delete_account(response: Response, user=Depends(current_user), db=Depends(database)):
    db.execute(text("DELETE FROM users WHERE id=:u"), {"u": user["id"]})
    response.delete_cookie("cg_session", path="/")
    return {"deleted": True}


@router.get("/profile")
def get_profile(user=Depends(current_user), db=Depends(database)):
    data = user_data.profile(db, user["id"])
    return {
        "profile": data,
        "completeness": sum(
            bool(data.get(k)) for k in ("name", "skills", "education", "projects", "graduation_year")
        )
        / 5,
    }


@router.put("/profile")
def update_profile(body: Profile, user=Depends(current_user), db=Depends(database)):
    user_data.save_profile(db, user["id"], body.model_dump())
    return body


@router.post("/profile/resume")
async def resume(file: UploadFile, hosted: bool = False, user=Depends(current_user)):
    if hosted and not user["provider_consent"]:
        raise HTTPException(403, "Provider consent required")
    data = await file.read(settings.upload_limit + 1)
    if len(data) > settings.upload_limit:
        raise HTTPException(413, "PDF exceeds upload limit")
    try:
        return {
            "profile": hosted_extract(pdf_text(data)) if hosted else parse_pdf(data),
            "parser": "provider-selected verified excerpts" if hosted else "local evidence extraction",
            "requires_confirmation": True,
            "retained": False,
        }
    except (httpx.HTTPError, KeyError, IndexError):
        raise HTTPException(502, "Provider extraction unavailable") from None
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None


class Consent(Strict):
    allowed: bool


@router.put("/privacy/provider-consent")
def consent(body: Consent, user=Depends(current_user), db=Depends(database)):
    db.execute(
        text("UPDATE users SET provider_consent=:allowed WHERE id=:u"),
        {"allowed": body.allowed, "u": user["id"]},
    )
    return body


@router.get("/preferences")
def preferences(user=Depends(current_user), db=Depends(database)):
    return {"preferences": user_data.preferences(db, user["id"])}


@router.put("/preferences")
def set_preferences(body: Preferences, user=Depends(current_user), db=Depends(database)):
    if any(len(p) > 300 or not p.strip() for p in body.preferences):
        raise HTTPException(422, "Each preference must contain 1–300 characters")
    db.execute(text("DELETE FROM candidate_preferences WHERE user_id=:u"), {"u": user["id"]})
    for preference in set(body.preferences):
        db.execute(
            text("INSERT INTO candidate_preferences(user_id,preference) VALUES(:u,:p)"),
            {"u": user["id"], "p": preference},
        )
    return body


@router.post("/jobs/search")
def search_jobs(body: Search, user=Depends(current_user), db=Depends(database)):
    return {
        "results": search(
            db,
            body,
            user_data.profile(db, user["id"]),
            user_data.preferences(db, user["id"]),
            str(user["id"]),
        )
    }


@router.post("/jobs/compare")
def compare(body: Comparison, user=Depends(current_user), db=Depends(database)):
    from app.agents.tools import dispatch

    return dispatch("compare_jobs", body.model_dump(mode="json"), db, user["id"], {})


@router.get("/jobs/{identifier}")
def detail(identifier: UUID, user=Depends(current_user), db=Depends(database)):
    job = user_data.job(db, identifier)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/saved-jobs")
def saved(user=Depends(current_user), db=Depends(database)):
    return [
        user_data.job(db, j)
        for j in db.execute(
            text("SELECT job_id FROM saved_jobs WHERE user_id=:u"), {"u": user["id"]}
        ).scalars()
    ]


@router.post("/saved-jobs")
def save(body: Saved, user=Depends(current_user), db=Depends(database)):
    if not user_data.job(db, body.job_id):
        raise HTTPException(404, "Job not found")
    db.execute(
        text("INSERT INTO saved_jobs(user_id,job_id) VALUES(:u,:j) ON CONFLICT DO NOTHING"),
        {"u": user["id"], "j": body.job_id},
    )
    return {"saved": True}


@router.delete("/saved-jobs/{identifier}")
def unsave(identifier: UUID, user=Depends(current_user), db=Depends(database)):
    db.execute(
        text("DELETE FROM saved_jobs WHERE user_id=:u AND job_id=:j"), {"u": user["id"], "j": identifier}
    )
    return {"removed": True}


@router.post("/feedback")
def feedback(body: Feedback, user=Depends(current_user), db=Depends(database)):
    from app.agents.tools import dispatch

    if not user_data.job(db, body.job_id):
        raise HTTPException(404, "Job not found")
    return dispatch("record_job_feedback", body.model_dump(mode="json"), db, user["id"], {}, True)


@router.post("/chat/sessions", status_code=201)
def create_session(user=Depends(current_user), db=Depends(database)):
    identifier = uuid4()
    db.execute(
        text("INSERT INTO search_sessions(id,user_id) VALUES(:i,:u)"), {"i": identifier, "u": user["id"]}
    )
    return {"id": identifier}


def owned_session(db, identifier, uid):
    row = (
        db.execute(
            text("SELECT * FROM search_sessions WHERE id=:i AND user_id=:u FOR UPDATE"),
            {"i": identifier, "u": uid},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(404, "Session not found")
    return dict(row)


@router.get("/chat/sessions/{identifier}/messages")
def messages(identifier: UUID, user=Depends(current_user), db=Depends(database)):
    owned_session(db, identifier, user["id"])
    return list(
        db.execute(
            text(
                "SELECT role,content,created_at FROM search_messages WHERE session_id=:i ORDER BY created_at,id"
            ),
            {"i": identifier},
        ).mappings()
    )


@router.post("/chat/sessions/{identifier}/messages")
def chat(identifier: UUID, body: Message, user=Depends(current_user), db=Depends(database)):
    state = owned_session(db, identifier, user["id"])
    state["recent_messages"] = list(
        reversed(
            db.execute(
                text(
                    "SELECT content FROM search_messages WHERE session_id=:i AND role='user' ORDER BY created_at DESC LIMIT 6"
                ),
                {"i": identifier},
            )
            .scalars()
            .all()
        )
    )
    result = respond(
        db, user["id"], state, body.message, local_only=not (body.allow_provider and user["provider_consent"])
    )
    db.execute(
        text(
            "UPDATE search_sessions SET query=:q,constraints=CAST(:c AS jsonb),last_jobs=CAST(:j AS jsonb),pending_preference=:p WHERE id=:i"
        ),
        {
            "q": state["query"],
            "c": json.dumps(state["constraints"]),
            "j": json.dumps(state["last_jobs"]),
            "p": state.get("pending_preference"),
            "i": identifier,
        },
    )
    for role, content in [("user", body.message), ("assistant", result)]:
        db.execute(
            text(
                "INSERT INTO search_messages(id,session_id,role,content) VALUES(:id,:s,:r,CAST(:c AS jsonb))"
            ),
            {"id": uuid4(), "s": identifier, "r": role, "c": json.dumps(jsonable_encoder(content))},
        )
    return result


@router.get("/evaluations")
def evaluations(user=Depends(current_user), db=Depends(database)):
    return list(
        db.execute(text("SELECT * FROM evaluation_runs ORDER BY created_at DESC LIMIT 30")).mappings()
    )


@router.get("/admin/ingestion")
def ingestion_runs(user=Depends(admin), db=Depends(database)):
    return list(db.execute(text("SELECT * FROM ingestion_runs ORDER BY created_at DESC LIMIT 30")).mappings())


@router.post("/admin/ingestion")
def import_jobs(body: list[Job], user=Depends(admin), db=Depends(database)):
    if len(body) > 2000:
        raise HTTPException(413, "Maximum batch is 2000 jobs")
    return ingest(db, [job.model_dump() for job in body])
