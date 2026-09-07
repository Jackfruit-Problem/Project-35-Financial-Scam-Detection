# Running FSDIRAS

Everything below assumes you are in the repository root.

## What you need installed

| Tool | Version | Needed for |
|---|---|---|
| Python | 3.11 or later | The backend and the test suite |
| Docker Desktop | any current | Running against PostgreSQL (optional for now) |

Docker is optional today. Without it the system runs on SQLite, a small
file-based database that needs no installation. The code is written so that
both behave the same, and CI runs the tests against real PostgreSQL to make
sure that stays true.

## First-time setup

From the `backend` folder:

```
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

That creates an isolated Python environment in `backend/.venv` and installs
everything into it. It does not touch your system Python.

## Load the demo data

```
.venv\Scripts\python.exe scripts/seed_demo.py
```

This wipes and rebuilds the local database with six accounts, five scam
reports across the risk bands, a case with a full evidence trail, a partially
recovered case, awareness articles and a quiz. Re-run it any time to get back
to a clean, known state -- useful right before a demo.

Every demo account uses the password `password123`:

| Role | Email |
|---|---|
| Victim | `victim@fsdiras.example.com` |
| Victim | `victim2@fsdiras.example.com` |
| Investigator | `investigator@fsdiras.example.com` |
| Investigator | `investigator2@fsdiras.example.com` |
| Recovery officer | `officer@fsdiras.example.com` |
| Administrator | `admin@fsdiras.example.com` |

## Start the server

```
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000/docs**.

That page is generated from the code itself, so it is always an accurate list
of what the system can do. Stop the server with `Ctrl+C`.

### Logging in on that page

1. Find `POST /api/v1/auth/login`, click **Try it out**
2. Replace the body with one of the accounts above and **Execute**
3. Copy the `access_token` value from the response
4. Click **Authorize** at the top right, paste the token, **Authorize**

Every request you make from the page now runs as that user. Log in as a
different role to see how the system's answers change -- that is the clearest
way to see role-based access control working.

## Run the tests

```
.venv\Scripts\python.exe -m pytest          # quiet
.venv\Scripts\python.exe -m pytest -v       # one line per test
.venv\Scripts\python.exe -m pytest tests/test_custody.py -v
```

The tests use their own throwaway in-memory database, so running them never
touches your demo data.

## Check code style

```
.venv\Scripts\python.exe -m ruff check .
```

CI runs this too, so a failure here is a failure there.

## Running on PostgreSQL with Docker

Once Docker Desktop is installed:

```
docker compose up
```

This starts PostgreSQL and the API together. The API is on
http://localhost:8000 as before. Stop with `Ctrl+C`, or `docker compose down`
to also remove the containers.

## Things worth trying

**See the risk engine work.** `POST /api/v1/detection/analyse` with any text.
Try a real scam message you have received and compare it with an ordinary
sentence. The response lists the reasons behind the score, not just a number.

**See role restrictions bite.** Log in as `victim2` and request a case that
belongs to `victim`. You get 403 Forbidden. Log in as an investigator who is
not assigned to a case and try to change its status -- also 403.

**Download a report.** `GET /api/v1/cases/{case_ref}/report.pdf` produces the
PDF that would go to a bank or the police.

**Break the chain of custody on purpose.** This is the most interesting thing
in the system to demonstrate. With the server running:

```
# 1. Verify evidence #1 -- chain_intact is true
curl http://127.0.0.1:8000/api/v1/evidence/1/verify -H "Authorization: Bearer YOUR_TOKEN"

# 2. Edit the database directly, bypassing the application entirely
cd backend
.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('fsdiras.db'); c.execute('UPDATE custody_events SET actor_id=99 WHERE id=2'); c.commit()"

# 3. Verify again -- chain_intact is now false, and it names the row
```

Nothing in the application was used to make that change, and it is still
detected, because each custody entry contains a hash of the one before it.
Re-run the seed script to restore everything.

## If something goes wrong

**`python` is not recognised** -- Python is not on your PATH. Reinstall it
with the "Add Python to PATH" box ticked, or use the full path to
`python.exe`.

**Port 8000 already in use** -- another copy of the server is still running.
Close that terminal, or start on a different port with `--port 8001`.

**Login returns 422 about the email** -- the address uses a reserved domain
such as `.local` or `.test`. Use a normal domain; the demo accounts use
`example.com`.

**Tests pass locally but fail in CI** -- CI runs on PostgreSQL and local runs
default to SQLite. Bring up Docker and set `DATABASE_URL` to the PostgreSQL
connection string to reproduce it.
