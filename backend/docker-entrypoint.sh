#!/bin/sh
# Bring the database up to date, then hand over to the API process.
#
# Every step here is idempotent, so a container restart is always safe:
#   * the probe only waits
#   * `alembic upgrade head` does nothing when the schema is current
#   * the seed only fills an empty catalogue (SEED_ON_START, first boot)
set -eu

log() {
    printf '[entrypoint] %s\n' "$*"
}

fail() {
    printf '[entrypoint] %s\n' "$*" >&2
    exit 1
}

[ -n "${DATABASE_URL:-}" ] || fail "DATABASE_URL is not set."

# ---- 1. Wait for PostgreSQL ------------------------------------------------
# Compose waits for the database healthcheck already, but a restarted database
# volume or a slower host still needs a few seconds of grace.
log "Waiting for the database..."
python - <<'PY'
import os
import sys
import time

from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]
timeout = float(os.environ.get("DB_WAIT_TIMEOUT_SECONDS", "90"))
deadline = time.time() + timeout
attempt = 0
last_error = None

while time.time() < deadline:
    attempt += 1
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print(f"[entrypoint] database reachable after {attempt} attempt(s)")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001 - any failure means "not ready yet"
        last_error = exc
        time.sleep(2)

print(f"[entrypoint] database unreachable after {timeout:.0f}s: {last_error}", file=sys.stderr)
sys.exit(1)
PY

# ---- 2. Migrations ---------------------------------------------------------
log "Applying migrations..."
alembic upgrade head

# ---- 3. First-boot seed ----------------------------------------------------
# A reseed rewrites lesson material and prices, so it must never run against a
# live catalogue on every restart. It only fires when the catalogue is empty.
if [ "${SEED_ON_START:-true}" = "true" ]; then
    needs_seed=$(
        python - <<'PY'
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Course

with SessionLocal() as db:
    print("yes" if db.scalar(select(Course.id).limit(1)) is None else "no")
PY
    )

    if [ "$needs_seed" = "yes" ]; then
        if [ -n "${ENV:-}" ] && [ "${ENV}" != "dev" ] && [ -z "${SEED_ADMIN_PASSWORD:-}" ]; then
            fail "SEED_ADMIN_PASSWORD must be set before the first boot can create the admin user."
        fi
        log "Empty catalogue - seeding admin and courses..."
        python scripts/seed.py
    else
        log "Catalogue already populated - skipping seed."
    fi
else
    log "SEED_ON_START is off - skipping seed."
fi

log "Starting: $*"
exec "$@"
