# syntax=docker/dockerfile:1
#
# Learnora API image.
#
#   docker build -t learnora-api ./backend
#
# Migrations and the first-boot seed run from the entrypoint, so the container
# is self-contained: start it against any PostgreSQL and it brings the schema up
# to date before serving traffic.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first: this layer only rebuilds when requirements.txt changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts

# Never serve traffic as root.
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin learnora \
    && chmod -R a+rX /app \
    && chown -R learnora:learnora /app

COPY --chmod=0755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

USER learnora

EXPOSE 8000

# The entrypoint probes PostgreSQL, applies migrations, then execs this.
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*", \
     "--log-level", "info"]
