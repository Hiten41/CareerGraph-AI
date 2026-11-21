import hashlib
from fastapi import Depends, HTTPException, Request
from argon2 import PasswordHasher
from sqlalchemy import text
from app.db.session import database

hasher = PasswordHasher()


def digest(token: str):
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(request: Request, db=Depends(database)):
    token = request.cookies.get("cg_session", "")
    user = (
        db.execute(
            text(
                "SELECT u.id,u.email,u.role,u.provider_consent,s.csrf FROM users u JOIN auth_sessions s ON s.user_id=u.id WHERE s.token_hash=:token AND s.expires_at>now()"
            ),
            {"token": digest(token)},
        )
        .mappings()
        .first()
    )
    if not user:
        raise HTTPException(401, "Sign in required")
    if (
        request.method not in ("GET", "HEAD", "OPTIONS")
        and request.headers.get("x-csrf-token") != user["csrf"]
    ):
        raise HTTPException(403, "Invalid CSRF token")
    return dict(user)


def admin(user=Depends(current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "Admin role required")
    return user
