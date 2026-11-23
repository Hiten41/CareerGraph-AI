import logging
import time
from collections import defaultdict, deque
from threading import Lock
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.routes import router
from app.core.config import settings
from app.db.session import engine

app = FastAPI(title="CareerGraph AI", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.include_router(router)
limits: dict[str, deque[float]] = defaultdict(deque)
lock = Lock()


@app.middleware("http")
async def guard(request: Request, call_next):
    identifier = str(uuid4())
    if request.method in ("POST", "PUT", "DELETE"):
        origin = request.headers.get("origin")
        if origin and origin != settings.web_origin:
            return JSONResponse({"detail": "Origin rejected"}, 403)
    try:
        length = int(request.headers.get("content-length", "0"))
    except ValueError:
        return JSONResponse({"detail": "Invalid content length"}, 400)
    if length > settings.upload_limit + 100000:
        return JSONResponse({"detail": "Request too large"}, 413)
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with lock:
        for stale in [k for k, v in limits.items() if not v or v[-1] < now - 60]:
            del limits[stale]
        queue = limits[key]
        while queue and queue[0] < now - 60:
            queue.popleft()
        if len(queue) >= 120:
            return JSONResponse({"detail": "Rate limit exceeded"}, 429, headers={"Retry-After": "60"})
        queue.append(now)
    try:
        response = await call_next(request)
    except Exception:
        logging.error("request_failed request_id=%s", identifier)
        response = JSONResponse({"detail": "Internal service error", "request_id": identifier}, 500)
    response.headers["X-Request-ID"] = identifier
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.get("/api/v1/health/live")
def live():
    return {"status": "ok"}


@app.get("/api/v1/health/ready")
def ready():
    try:
        with engine.connect() as db:
            db.execute(text("SELECT provider_consent,recovery_hash FROM users LIMIT 0"))
        return {"status": "ready"}
    except Exception:
        return JSONResponse({"status": "database unavailable or not migrated"}, 503)
