import json
from sqlalchemy import text


def profile(db, uid):
    return db.execute(text("SELECT data FROM candidate_profiles WHERE user_id=:u"), {"u": uid}).scalar() or {}


def preferences(db, uid):
    return list(
        db.execute(
            text("SELECT preference FROM candidate_preferences WHERE user_id=:u ORDER BY preference"),
            {"u": uid},
        ).scalars()
    )


def save_profile(db, uid, data):
    db.execute(
        text(
            "INSERT INTO candidate_profiles(user_id,data) VALUES(:u,CAST(:d AS jsonb)) ON CONFLICT(user_id) DO UPDATE SET data=EXCLUDED.data,updated_at=now()"
        ),
        {"u": uid, "d": json.dumps(data)},
    )


def job(db, identifier):
    row = (
        db.execute(
            text(
                "SELECT id,title,company,description,skills,optional_skills,employment,mode,location,graduation_year,salary,currency,period,experience,domain,status,url,synthetic,last_seen_at FROM jobs WHERE id=:id"
            ),
            {"id": identifier},
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None
