# Deployment

Sprint 2 action item 2. Everything the deployment needs is committed; the one
step nobody but the account owner can do is connecting the repository to a
hosting account, which takes about ten minutes and is written out below.

## What is already in place

| Piece | Where | State |
|---|---|---|
| API container | `backend/Dockerfile` | ready |
| Model container | `ml/Dockerfile` | ready |
| Local full stack | `docker-compose.yml` | ready (needs Docker installed) |
| Hosted blueprint | `render.yaml` | ready |
| Schema creation | Alembic, run automatically at start-up | ready |
| Production config guard | `app/core/config.py` | ready |

The API runs `alembic upgrade head` as it boots, so a fresh database gets the
full schema with no manual step, and a later schema change is applied by the
same deploy that ships it.

## The production safety guard

With `FSDIRAS_ENV=production` the application **refuses to start** if:

- `SECRET_KEY` is still the development value, or is shorter than 32 characters
- `DATABASE_URL` points at SQLite

This is deliberate. A deployment that silently came up on SQLite with a known
signing key would look healthy and be worthless. In development the same checks
only warn.

## Deploying to Render (free tier)

1. Push the repository to GitHub — already done.
2. Create an account at <https://render.com> and authorise the GitHub org.
3. **New → Blueprint**, select `Project-35-Financial-Scam-Detection`.
   Render reads `render.yaml` and proposes four services:
   `fsdiras-db`, `fsdiras-ml`, `fsdiras-api`, `fsdiras-web`.
4. **Apply.** First build takes roughly 10–15 minutes, most of it installing
   scikit-learn into the model image.
5. If Render assigns the API a hostname other than
   `fsdiras-api.onrender.com`, edit the rewrite `destination` in `render.yaml`
   to match and push again. That URL is the only hard-coded value.
6. Open the `fsdiras-web` URL. Register an account, or seed the demo data:
   from the Render shell on `fsdiras-api`, run `python scripts/seed_demo.py`.

### Free-tier caveats, so nothing is a surprise in the demo

- Free web services **sleep after 15 minutes idle**; the first request afterwards
  takes 30–60 seconds. Open the site a minute before demonstrating it.
- A free PostgreSQL instance **expires after 30 days**. If the demo is later
  than that, create a fresh one and redeploy.
- Free instances have 512 MB RAM. The model service loads a 558 KB model, so it
  fits, but do not expect to train on the instance.

## Alternative: Railway or Fly.io

The same two Dockerfiles work. Set these environment variables on the API
service and point the SPA's `/api` rewrite at it:

```
DATABASE_URL=postgresql+psycopg://<user>:<pass>@<host>:5432/<db>
SECRET_KEY=<32+ random characters>
FSDIRAS_ENV=production
ML_SERVICE_URL=http://<ml-service-host>:8001
```

## Running the whole stack locally with Docker

Docker is not installed on the current development machine, which is why SQLite
is the local fallback. Where Docker is available:

```
docker compose up --build
```

API on <http://localhost:8000>, model on <http://localhost:8001>, PostgreSQL on
5432. This is the closest local match to the hosted setup, and the one to use
when checking anything database-dialect-specific.

## Verifying a deployment

```
curl https://<api-host>/health          # {"status":"ok","service":"FSDIRAS"}
curl https://<ml-host>/health           # {"status":"ok","model_version":"..."}
```

Then in the browser: register, run a message through the checker, submit a
report, and confirm a Case ID comes back. That exercises the database, the model
service and the fallback path in one pass.
