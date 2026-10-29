# Learnora native AWS deployment

This is the supported production deployment path for Learnora. It does not use
Docker or Docker Hub.

```text
GitHub Actions
      |
      v
Ubuntu EC2: nginx -> React build
                 \-> FastAPI systemd service
                              |
                              v
                    Amazon RDS PostgreSQL
```

## AWS resources

Create:

- Ubuntu Server 24.04 LTS EC2 instance (a `t3.small` is a reasonable starting point)
- Elastic IP associated with the EC2 instance
- Amazon RDS PostgreSQL in the same VPC
- DNS `A` record pointing the domain to the Elastic IP

The EC2 security group should allow:

| Protocol | Port | Source |
|---|---:|---|
| SSH | 22 | Your IP address only |
| HTTP | 80 | `0.0.0.0/0` |
| HTTPS | 443 | `0.0.0.0/0` |

Do not expose port `8000` or PostgreSQL port `5432` publicly. The RDS security
group should allow PostgreSQL port `5432` only from the EC2 security group.
Disable public access for RDS, enable encryption, backups, and deletion
protection for production.

## EC2 prerequisites

Connect as the Ubuntu user, then install the runtime:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-pip nginx \
  postgresql-client curl
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

Verify:

```bash
python3 --version
node --version
npm --version
nginx -v
```

## First deployment

Clone the repository:

```bash
sudo git clone https://github.com/Suryachow/Learnora.git /opt/learnora
sudo chown -R ubuntu:ubuntu /opt/learnora
cd /opt/learnora
```

Create the protected production environment file:

```bash
sudo mkdir -p /etc/learnora
sudo cp deploy/learnora.env.example /etc/learnora/learnora.env
sudo nano /etc/learnora/learnora.env
sudo chmod 600 /etc/learnora/learnora.env
```

Set real values:

```env
ENV=production
DATABASE_URL=postgresql+psycopg://DB_USER:DB_PASSWORD@RDS_ENDPOINT:5432/skillearn
JWT_SECRET=LONG_UNIQUE_RANDOM_VALUE
CORS_ORIGINS=https://your-domain.example
SEED_ON_START=true
SEED_ADMIN_NAME=Learnora Admin
SEED_ADMIN_EMAIL=admin@your-domain.example
SEED_ADMIN_PASSWORD=LONG_UNIQUE_ADMIN_PASSWORD
PAYMENT_PROVIDER=mock
REWARDS_ENABLED=true
```

Generate a secret without putting it in the repository:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

`DATABASE_URL` must be PostgreSQL in production. Do not use SQLite. If the
database password contains URL-reserved characters, URL-encode it.

Deploy:

```bash
cd /opt/learnora
chmod +x deploy/native-deploy.sh
sudo -E ./deploy/native-deploy.sh
```

The script creates the restricted `learnora` user, creates the Python virtual
environment, installs dependencies, runs Alembic migrations, seeds an empty
catalogue when enabled, builds the frontend, installs systemd and nginx
configuration, and starts both services.

After the first successful seed, set this in the environment file:

```env
SEED_ON_START=false
```

## Verification

```bash
sudo systemctl status learnora-api nginx
curl http://127.0.0.1/api/v1/health
curl http://127.0.0.1/api/v1/health/ready
curl http://YOUR_ELASTIC_IP/api/v1/health/ready
```

Logs:

```bash
sudo journalctl -u learnora-api --no-pager -n 100
sudo journalctl -u learnora-api -f
sudo tail -f /var/log/nginx/error.log
```

## Domain and HTTPS

Point an `A` record at the Elastic IP, then install TLS:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.example
sudo certbot renew --dry-run
```

Update `CORS_ORIGINS` to the exact HTTPS origin and redeploy:

```bash
sudo nano /etc/learnora/learnora.env
cd /opt/learnora
sudo -E ./deploy/native-deploy.sh
```

## GitHub Actions deployment

`.github/workflows/ci.yml` runs backend tests and the frontend production build
on pull requests and pushes. A successful push to `main` runs `deploy-native`,
which SSHes to EC2 and runs:

```bash
sudo -E APP_DIR=/opt/learnora ./deploy/native-deploy.sh
```

Create a GitHub environment named `production`, restrict it to the `main`
branch, and add these secrets:

| Secret | Value |
|---|---|
| `DEPLOY_HOST` | EC2 Elastic IP or DNS hostname |
| `DEPLOY_USER` | `ubuntu` |
| `DEPLOY_PATH` | `/opt/learnora` |
| `DEPLOY_SSH_KEY` | Contents of a dedicated EC2 deployment private key |

Install the matching public key in the EC2 user's
`~/.ssh/authorized_keys`. The EC2 user must be able to run the deployment
script with `sudo` without an interactive password prompt. Use a restricted
sudoers rule where possible.

Do not add passwords, JWT secrets, RDS credentials, payment keys, `.env` files,
or private keys to GitHub source files or commit history.

## Updates and rollback

Manual update:

```bash
cd /opt/learnora
sudo -E ./deploy/native-deploy.sh
```

The script fast-forwards the `main` checkout, applies migrations, rebuilds the
frontend, and restarts the API. Take an RDS snapshot before high-risk schema
changes. If an update fails, inspect the systemd journal and restore the
previous Git commit only after confirming the database migration is compatible.

Never delete production database storage. RDS backups and point-in-time
recovery should be enabled before launch.

## Cache strategy

The deployment uses nginx/browser caching for hashed frontend assets. It does
not cache authenticated API responses. Do not initially cache wallet, payment,
transaction, progress, quiz-attempt, authentication, or admin responses.

Add Amazon ElastiCache Redis or Valkey only after the first deployment is
stable. Start with short-lived public catalogue keys such as
`catalogue:courses:v1` and `catalogue:course:{id}:v1`. Invalidate them when
catalogue content changes. Include the user ID in any future user-specific key.
