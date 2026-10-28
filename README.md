# Learnora

Learn practical technical and professional skills, pass assessments, and earn rewards. Rewards
are funded by subscriptions, so the platform only pays what it can cover.

- **Backend:** FastAPI · SQLAlchemy 2 · Alembic · Pydantic v2 · PostgreSQL · pytest
- **Frontend:** React 18 · Vite · React Router · plain CSS with design tokens
- **Light and dark themes**, plus an admin console for the catalogue, quizzes, users and the
  business settings.

```
skillearn/
  backend/    app/{config,db,deps,main}.py  app/{models,schemas,routers,services}/  alembic/  scripts/  tests/
  frontend/   src/{api,components,hooks,pages,styles,utils}/
              src/pages/settings/   account settings sections
              src/pages/admin/      the admin console
```

## 1. Prerequisites

- Python 3.11+ (developed on 3.14)
- Node.js 20+ (developed on 24)

## 2. Backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

Copy-Item .env.example .env           # macOS/Linux: cp .env.example .env
# Open .env, set DATABASE_URL to your PostgreSQL connection, and set JWT_SECRET
# to a long random value:
#   python -c "import secrets; print(secrets.token_urlsafe(48))"

alembic upgrade head                  # create the tables
python scripts/seed.py                # admin + the C and Python courses + their quizzes
uvicorn app.main:app --reload --port 8000
```

- API docs: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/api/v1/health>
- Seeded admin: `admin@skillearn.dev` / `Admin@12345` (override with `SEED_ADMIN_EMAIL` /
  `SEED_ADMIN_PASSWORD`). **Change this before any real deployment.**
- Sign in as that admin and open `/admin` for the console (overview, users, courses and topics,
  tasks and quiz builder, settings). The link also appears in the account menu.

## 3. Frontend setup

```powershell
cd frontend
npm install
npm run dev            # http://localhost:5173
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`, so the browser talks to one origin.
To point at a different backend, copy `.env.example` to `.env` and set `VITE_API_BASE_URL`.

## 4. Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

The suite uses its own throwaway SQLite database and never touches your dev data. It covers auth,
the catalogue, grading and reward rules (pay-once, daily limit, per-task cap, kill switch), the
subscription webhook, the admin API (403 for learners, answers visible only to admins) and
account self-service.

## 5. Environment variables (`backend/.env`)

Only deployment wiring and secrets stay here. Every **business** knob below is also editable at
runtime from **Admin → Settings** (`app_settings` overrides the `.env` default, effective on the
next request, resettable per key).

| Variable | Default | Purpose |
|---|---|---|
| `ENV` | `dev` | `prod` disables dev-only behaviour and refuses the placeholder JWT secret |
| `DATABASE_URL` | `postgresql+psycopg://postgres:<password>@localhost:5432/skillearn` | PostgreSQL connection URL |
| `JWT_SECRET` | placeholder | Signs access tokens. Must be replaced in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime |
| `CORS_ORIGINS` | `http://localhost:5173,…` | Comma-separated browser origins |
| `SUBSCRIPTION_PRICE_PAISE` | `14900` | Plan price (₹149) in paise · editable in the console |
| `SUBSCRIPTION_DAYS` | `30` | Days added by one successful payment · editable in the console |
| `REWARDS_ENABLED` | `true` | Global kill switch for granting rewards · editable in the console |
| `REWARD_DAILY_LIMIT_PAISE` | `50000` | Max rewards one user can earn per day · editable in the console |
| `REWARD_PER_TASK_LIMIT_PAISE` | `20000` | Max reward a single task may pay · editable in the console |
| `REWARD_MAX_PERCENT_OF_REVENUE` | `50` | Admin report warns above this rewards/revenue ratio · editable in the console |
| `ATTEMPT_COOLDOWN_SECONDS` | `10` | Minimum gap between two submissions on one task · editable in the console |
| `SUBMISSION_RATE_LIMIT_PER_MINUTE` | `20` | Submission rate limit per user · editable in the console |
| `PAYMENT_PROVIDER` | `mock` | `mock` (local dev) or `razorpay` |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` / `RAZORPAY_WEBHOOK_SECRET` | – | Razorpay credentials |
| `GROQ_API_KEY` | – | Optional. Enables `scripts/generate_quizzes.py`; the shipped quizzes need no key |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Model used to write quiz questions |
| `QUIZ_QUESTIONS_PER_TOPIC` | `5` | How many questions each generated quiz asks |

Never commit `.env`. Only `.env.example` belongs in the repository.

## 6. Money rules

- All amounts are **integer paise** (₹1 = 100). Floats are never used for money.
- `transactions` is an **append-only ledger**; the wallet balance is computed from it and is never
  stored as a mutable number.
- `UNIQUE (user_id, task_id, kind)` means a reward can be recorded at most once per task.
- All timestamps are stored as naive UTC.
- A course can be paid two ways: from the wallet (`course_purchase`, which debits the balance) or
  through the payment gateway (`course_payment`, revenue only). Both count as course revenue;
  only the first moves the wallet.

## 7. Design system

Warm canvas `#E8E7E3` · white `#FFFFFF` cards with 22px corners · near-black `#17171A` for
navigation, buttons and headings · sage green `#5C7B63` for the single accent card and the admin
rail entry · main text `#17171A` · secondary text `#6E6E68` · borders `#E5E3DC`. Type is Sora
(variable, self-hosted in `frontend/src/assets/fonts`).

**Gold `#D4A72C` is reserved for wallet balances, earnings and reward amounts.** Because `#D4A72C`
on white is only ~2.2:1 contrast, reward *text* uses `--color-gold-text: #8A6D0B` (~4.9:1) while
gold itself is used for borders, badges and accents. Tokens live in
`frontend/src/styles/tokens.css`; the shared shell lives in `frontend/src/styles/shell.css`.

Every signed-in page is drawn inside that shell: a floating 72px icon rail
(`components/AppRail.jsx`), a utility row with the sunburst mark, catalogue search and theme
switch (`components/TopBar.jsx`), then the page body. Landing, sign-in and sign-up keep the canvas
without the rail. The admin console keeps its own shell (`pages/admin/AdminLayout.jsx`).

## 8. Production deployment on AWS without Docker

The recommended AWS deployment is an Ubuntu EC2 instance running the API with
systemd and serving the built React application through nginx. Use Amazon RDS
for PostgreSQL rather than running the database on the EC2 instance.

On the EC2 instance, install the runtime prerequisites:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nginx nodejs npm
```

Create the application environment file and protect it:

```bash
sudo mkdir -p /etc/learnora
sudo cp deploy/learnora.env.example /etc/learnora/learnora.env
sudo nano /etc/learnora/learnora.env
sudo chmod 600 /etc/learnora/learnora.env
```

Set a real RDS `DATABASE_URL`, a long random `JWT_SECRET`, your public
`CORS_ORIGINS`, and a strong first-boot `SEED_ADMIN_PASSWORD`. Set
`PAYMENT_PROVIDER=razorpay` only after all Razorpay secrets are configured.
Set `SEED_ON_START=false` after the initial catalogue has been created.

Run the native deployment script:

```bash
git clone https://github.com/Suryachow/Learnora.git /opt/learnora
cd /opt/learnora
chmod +x deploy/native-deploy.sh
sudo -E ./deploy/native-deploy.sh
```

The script pulls the latest `main` branch on subsequent runs, creates the
backend virtual environment, installs dependencies, runs Alembic migrations,
seeds an empty catalogue when enabled, builds the frontend, installs the
systemd service, and configures nginx.

Verify the native deployment:

```bash
sudo systemctl status learnora-api nginx
curl http://127.0.0.1/api/v1/health/ready
```

For a public deployment, point DNS to the EC2 Elastic IP, allow TCP 80/443 in
the security group, and add TLS with Certbot:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.example
```

Deploy later GitHub updates with:

```bash
cd /opt/learnora
sudo -E ./deploy/native-deploy.sh
```

Logs are available with:

```bash
sudo journalctl -u learnora-api -f
sudo tail -f /var/log/nginx/error.log
```

## 9. Optional Docker deployment

The repository also includes a Docker Compose stack, but Docker is not required
for the AWS deployment above. GitHub stores the source; Docker images must be
rebuilt after each source update.

1. Clone the repository and enter the project:

   ```powershell
   git clone https://github.com/Suryachow/Learnora.git
   cd Learnora
   ```

2. Create the deployment environment file without committing it:

   ```powershell
   Copy-Item .env.docker.example .env.docker
   ```

   Set unique values for `POSTGRES_PASSWORD`, `JWT_SECRET`, and
   `SEED_ADMIN_PASSWORD`. Use `PAYMENT_PROVIDER=razorpay` with valid Razorpay
   secrets before enabling real payments. Keep `.env.docker` outside GitHub.

3. Build and start the stack:

   ```powershell
   docker compose --env-file .env.docker up -d --build
   ```

   The website is available at `http://localhost:8080` by default. Put a TLS
   reverse proxy in front of this port for a public domain and update
   `CORS_ORIGINS` to that exact origin.

4. Verify the deployment:

   ```powershell
   docker compose --env-file .env.docker ps
   Invoke-WebRequest http://localhost:8080/api/v1/health/ready
   ```

   All three services should be healthy and the readiness response should
   report `"database": "up"`.

5. Deploy a GitHub update:

   ```powershell
   git pull origin main
   docker compose --env-file .env.docker up -d --build
   ```

   Compose runs Alembic migrations during API startup. The database is stored
   in the named `db_data` volume and is not removed by a normal rebuild.
   Never use `docker compose down -v` on a deployment unless the database is
   intentionally being destroyed.

The GitHub Actions workflow at `.github/workflows/ci.yml` runs backend tests,
the frontend production build, Compose validation, and both application image
builds for pushes and pull requests targeting `main`.

## 10. Build status

| Phase | Scope | Status |
|---|---|---|
| 1 | Scaffolding, config, models, migrations, auth, design tokens, layout/nav | ✅ done |
| 2 | Courses, topics, materials, video embeds | ✅ done (C and Python, 38 lessons, YouTube embeds) |
| 3 | Quiz engine, server grading, attempts, one-reward-per-task | ✅ done |
| 4 | Subscription and course checkout + webhook, ledger, wallet, transaction history | ✅ done |
| 5 | Admin console: courses, topics, tasks/quiz builder, users, reports, settings | ✅ done |
| 6 | Account settings, rewards policy, light/dark polish | ✅ done (certificates remain a placeholder) |

### The catalogue

Learnora teaches two courses and teaches them end to end. The lessons live in
`backend/scripts/catalogue/` — `c_course.py` and `python_course.py` — so the syllabus is
reviewable code, not database rows somebody has to reconstruct.

| Course | Lessons | Price to unlock | Path |
|---|---|---|---|
| C Programming | 18 | ₹349 | toolchain → types, pointers, memory, structs, files, build tools → a finished CLI project |
| Python Programming | 20 | ₹349 | interpreter → collections, functions, errors, modules, classes, generators, typing, stdlib, tests, concurrency → a packaged CLI |

Every lesson carries a YouTube video the learner must finish and one quiz whose questions are
stored on the task and graded by the server. `python scripts/seed.py` is idempotent: it republishes
lesson material when the catalogue changes and retires any course the catalogue no longer defines,
so reseeding a database that still holds the old eight-course sample leaves exactly C and Python.

### Buying a paid course

Both courses cost **₹349**. The price is part of the catalogue (`price_paise`, in paise) and the
seed applies it, so moving a course between free and paid is a code change, not a database edit.

A locked lesson withholds its notes and video, and its assessments stay closed, until the course is
bought. The learner's path is: course page → **Select this course — ₹349** → `/checkout/{id}` →
**Pay ₹349** → confirmed → the course opens. Underneath, the flow has the same shape as the
subscription, so the production gateway drops straight in:

1. `POST /courses/{id}/checkout` prices the course from the catalogue — never from the browser — and
   opens a gateway order whose receipt is `course-<id>`.
2. The provider sends a signed callback to `POST /courses/payments/webhook`.
3. The server verifies the signature, then writes one negative `course_payment` row (keyed by the
   order id, so a replayed webhook changes nothing) and opens the `course_purchases` entitlement.

With `PAYMENT_PROVIDER=mock` and `ENV=dev`, the button on a course page calls
`POST /courses/{id}/dev/simulate-payment`, which builds that callback server-side, signs it with the
same secret and runs it through the same verification. Nothing in the browser can unlock a course on
its own. A gateway payment never touches the reward wallet; `POST /courses/{id}/purchase` (pay from
the wallet, `course_purchase`) is still available for learners spending earned rewards.

### Writing quizzes with Groq

The shipped quizzes are complete and work with no API key. With `GROQ_API_KEY` set in
`backend/.env`, the questions can instead be written from each lesson's own notes:

```powershell
python scripts/generate_quizzes.py --course C --limit 2   # try two lessons first
python scripts/generate_quizzes.py --missing-only         # fill gaps only
python scripts/generate_quizzes.py                        # rewrite every quiz
```

Generation is a build-time step on purpose: questions are stored once and graded on the server, so
the same quiz is marked the same way on every attempt. Everything the model returns is treated as
untrusted — a question is kept only if it has a prompt, four distinct options and one valid
`correct_index`, and an unusable reply raises instead of writing a broken quiz.

The free tier meters **tokens per minute**, so a run across 38 lessons is throttled part way
through. The client waits for the interval the 429 names and retries the same lesson, and a reply
with too few gradeable questions is asked again rather than left unfinished — so a first run ends
with every lesson written. Re-running only the lessons you care about works the same way:
`--course Python --limit 5`.

### How an attempt pays

1. `GET /tasks/{id}/quiz` returns prompts and options — never `correct_index`.
2. `POST /tasks/{id}/attempts` grades on the server, then hands the outcome to
   `services/rewards.py`, which decides pass, kill switch, daily limit and per-task cap.
3. The ledger row is written in the same transaction as the attempt, so a pass and its reward can
   never disagree. `UNIQUE (user_id, task_id, kind)` makes the payout once-only.

### Frontend route map

Public: `/` (landing) · `/courses` · `/courses/:courseId` · `/topics/:topicId` · `/rewards-policy`
Guests only: `/login` · `/signup`
Signed in: `/dashboard` · `/checkout/:courseId` · `/tasks/:taskId` (quiz runner) · `/subscription` ·
`/wallet` · `/transactions` · `/certificates`
Settings: `/settings` → `/settings/{profile,security,preferences,billing}` (`/profile` redirects)
Admin (`user.is_admin` only, own shell): `/admin` · `/admin/users` · `/admin/courses` ·
`/admin/tasks` · `/admin/settings` — courses and topics are created, edited, deleted and reordered
by hand from `/admin/courses`, and the console is one click away from the rail (shield icon).

Source modules: `src/api/{catalog,subscription,wallet,auth,attempts,account,admin,client}.js`,
`src/hooks/{useAuth,useFetch}.js`,
`src/components/{Amount,Modal,Switch,Tabs,Badge,ProgressBar,ThemeToggle,Alert,Button,FormField,…}.jsx`,
`src/utils/{money,datetime}.js`, `src/pages/**`, tokens in `src/styles/tokens.css`.

## 9. Stubbed or deferred (deliberate)

- **Coding tasks** — only quizzes are implemented. The quiz builder creates quiz tasks; a coding
  task is refused by `GET /tasks/{id}/quiz` until a sandboxed runner exists. User code must never
  run inside the API process.
- **Certificates** — the page explains the intended behaviour but issues nothing yet; certificates
  will be generated once topic completion is tracked.
- **Withdrawals** — payout execution is owned by another team. The ledger and a `withdrawal`
  transaction kind are provided; no payout logic is implemented.
- **Payment provider** — the mock provider is for local development only and is disabled when
  `ENV=prod`. In both modes the signed webhook is the only path that activates a subscription.
- **Progress table** — topic progress is derived from attempts rather than stored, so it can never
  drift out of sync with the grading records.
- **Email** — preference switches are stored per user, but no mail is actually sent yet.

## 10. Deploying with Docker

`docker-compose.yml` runs the whole product: PostgreSQL, the API and nginx serving the built SPA.
Only the web container publishes a port, so the database and the API are never exposed directly.

```powershell
cd skillearn
Copy-Item .env.docker.example .env.docker
# Open .env.docker and set POSTGRES_PASSWORD, JWT_SECRET and SEED_ADMIN_PASSWORD.
#   python -c "import secrets; print(secrets.token_urlsafe(48))"

docker compose --env-file .env.docker up -d --build
docker compose --env-file .env.docker logs -f api
```

The site is then on <http://localhost:8080> (or `HTTP_PORT`). The API is behind `/api`, so
<http://localhost:8080/api/v1/health> answers too.

| Image | What it does |
|---|---|
| `learnora-api` | `python:3.12-slim`, non-root. The entrypoint waits for PostgreSQL, runs `alembic upgrade head`, seeds the catalogue on a first boot, then starts uvicorn with `--proxy-headers`. |
| `learnora-web` | `node:20-alpine` builds the bundle, `nginx:1.27-alpine` serves it with gzip, security headers and an `/api` proxy. |

Notes for running it for real:

- **Secrets live in `.env.docker` only** and it is git-ignored. The API refuses to start with the
  shipped placeholder `JWT_SECRET` when `ENV=production`.
- **The seed runs once.** It only fills an empty catalogue, so restarting containers never rewrites
  lesson material or resets the admin password. Set `SEED_ON_START=false` once the site is live.
- **`POSTGRES_PASSWORD` must be URL-safe** (`A-Z a-z 0-9 - _ .`) because it is embedded in
  `DATABASE_URL`. A `@`, `:` or `/` there breaks the connection string.
- **TLS is not terminated here.** Put Caddy, Traefik or your cloud load balancer in front of
  `HTTP_PORT`, and set `CORS_ORIGINS` to the public origin.
- **Backups** are the `db_data` volume: `docker compose exec db pg_dump -U skillearn skillearn > backup.sql`.
- **Health**: `/api/v1/health` is a liveness probe, `/api/v1/health/ready` also proves the database
  is reachable (it returns 503 when it is not). Compose healthchecks poll both.
- **Payments are unchanged.** With `PAYMENT_PROVIDER=mock` and `ENV=production` the mock provider is
  inert, so checkout will not complete until Razorpay keys are configured — paid courses stay locked
  until then.
