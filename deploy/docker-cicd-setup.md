# Docker CI/CD setup

The `main` branch workflow in `.github/workflows/ci.yml`:

1. Runs backend tests and the frontend build.
2. Builds the Docker images.
3. Publishes immutable SHA-tagged images and `latest` tags to Docker Hub.
4. Deploys the SHA-tagged images to EC2 when the production deployment secrets exist.

The deployment uses Amazon RDS or the existing database volume from the server's
`.env.docker` file. It never replaces the database volume.

## EC2 preparation

Install Docker Compose on Ubuntu, clone the repository, and create the production
environment file:

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker

sudo mkdir -p /opt/learnora
sudo chown "$USER:$USER" /opt/learnora
cd /opt/learnora
cp .env.docker.example .env.docker
chmod 600 .env.docker
```

Set the real production values in `.env.docker`, including `JWT_SECRET`,
`POSTGRES_PASSWORD`, `CORS_ORIGINS`, and `SEED_ADMIN_PASSWORD`. Keep this file
on EC2 only; never commit it.

For the first deployment, start the stack manually:

```bash
docker compose --env-file .env.docker up -d
docker compose --env-file .env.docker ps
```

## GitHub Actions secrets

Create the Docker Hub repositories `learnora-api` and `learnora-web` under
the `suyatama` account. Then create a GitHub **production environment** and add
these secrets:

| Secret | Value |
|---|---|
| `DEPLOY_HOST` | EC2 Elastic IP or DNS hostname |
| `DEPLOY_USER` | `ubuntu` |
| `DEPLOY_SSH_KEY` | Contents of the EC2 private key |
| `DEPLOY_PATH` | `/opt/learnora` |
| `DOCKERHUB_USERNAME` | `suyatama` |
| `DOCKERHUB_TOKEN` | Docker Hub access token, not your password |

Create the Docker Hub token at Docker Hub → Account Settings → Security →
Personal access tokens. Give it read/write permission, copy it once, and save it
as `DOCKERHUB_TOKEN`. The workflow logs in to Docker Hub during each deployment
and does not store the token in the repository.

Add the EC2 user's public key to `~/.ssh/authorized_keys` before enabling the
deployment job. Restrict the key to this repository's deployment purpose where
your SSH policy supports it.

## Deployment behavior

Every successful push to `main` deploys the exact commit SHA, not a mutable
`latest` tag. The old containers are replaced only after Docker has pulled the
new images. Migrations run from the API container entrypoint. The PostgreSQL
volume is retained by normal `up` and `down` commands; never use
`docker compose down -v` on production.
