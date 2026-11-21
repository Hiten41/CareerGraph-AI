#!/bin/bash
set -euo pipefail
: "${RENDER_EXTERNAL_URL:?Public HTTPS origin is required}"
: "${DATABASE_URL:?Database connection is required}"
export WEB_ORIGIN="$RENDER_EXTERNAL_URL"
export DATABASE_URL="${DATABASE_URL/#postgresql:\/\//postgresql+psycopg:\/\/}"
export HOSTNAME=0.0.0.0
export PORT="${PORT:-10000}"
alembic -c apps/api/alembic.ini upgrade head
python scripts/seed.py

uvicorn app.main:app --host 127.0.0.1 --port 8000 --limit-concurrency 12 &
api=$!
node /web/server.js &
web=$!
trap 'kill "$api" "$web" 2>/dev/null || true' EXIT
trap 'exit 0' INT TERM
wait -n "$api" "$web"
