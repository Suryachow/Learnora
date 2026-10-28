#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/learnora}"
ENV_FILE="${ENV_FILE:-/etc/learnora/learnora.env}"
REPO_URL="${REPO_URL:-https://github.com/Suryachow/Learnora.git}"
BRANCH="${BRANCH:-main}"

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

log() { printf '[learnora-deploy] %s\n' "$*"; }
fail() { printf '[learnora-deploy] ERROR: %s\n' "$*" >&2; exit 1; }

command -v git >/dev/null || fail "git is required."
command -v python3 >/dev/null || fail "python3 is required."
command -v npm >/dev/null || fail "npm is required."
command -v nginx >/dev/null || fail "nginx is required."
[[ -f "${ENV_FILE}" ]] || fail "Create ${ENV_FILE} with production secrets first."

if ! id learnora >/dev/null 2>&1; then
  $SUDO useradd --system --home-dir "${APP_DIR}" --shell /usr/sbin/nologin learnora
fi

if [[ ! -d "${APP_DIR}/.git" ]]; then
  $SUDO mkdir -p "$(dirname "${APP_DIR}")"
  $SUDO git clone --branch "${BRANCH}" "${REPO_URL}" "${APP_DIR}"
else
  $SUDO git -C "${APP_DIR}" fetch origin "${BRANCH}"
  $SUDO git -C "${APP_DIR}" checkout "${BRANCH}"
  $SUDO git -C "${APP_DIR}" pull --ff-only origin "${BRANCH}"
fi

$SUDO mkdir -p /etc/learnora
$SUDO chown -R "$(id -u):$(id -g)" "${APP_DIR}"

log "Installing backend dependencies..."
python3 -m venv "${APP_DIR}/backend/.venv"
"${APP_DIR}/backend/.venv/bin/pip" install --upgrade pip --quiet
"${APP_DIR}/backend/.venv/bin/pip" install -r "${APP_DIR}/backend/requirements.txt" --quiet

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a
[[ "${ENV:-}" == "production" || "${ENV:-}" == "prod" ]] || fail "ENV must be production."
[[ -n "${DATABASE_URL:-}" ]] || fail "DATABASE_URL is required."
[[ -n "${JWT_SECRET:-}" ]] || fail "JWT_SECRET is required."

log "Applying database migrations..."
(cd "${APP_DIR}/backend" && .venv/bin/alembic upgrade head)

if [[ "${SEED_ON_START:-false}" == "true" ]]; then
  log "Seeding the catalogue when the database is empty..."
  (cd "${APP_DIR}/backend" && .venv/bin/python scripts/seed.py)
fi

log "Building frontend..."
(cd "${APP_DIR}/frontend" && npm ci --no-audit --no-fund && npm run build)

$SUDO chown -R learnora:learnora "${APP_DIR}"
$SUDO install -m 0644 "${APP_DIR}/deploy/learnora-api.service" /etc/systemd/system/learnora-api.service
$SUDO install -m 0644 "${APP_DIR}/deploy/learnora.nginx.conf" /etc/nginx/sites-available/learnora
$SUDO ln -sfn /etc/nginx/sites-available/learnora /etc/nginx/sites-enabled/learnora
$SUDO rm -f /etc/nginx/sites-enabled/default
$SUDO nginx -t
$SUDO systemctl daemon-reload
$SUDO systemctl enable --now learnora-api
$SUDO systemctl restart learnora-api
$SUDO systemctl enable --now nginx
$SUDO systemctl reload nginx

log "Deployment complete. Check: systemctl status learnora-api nginx"
