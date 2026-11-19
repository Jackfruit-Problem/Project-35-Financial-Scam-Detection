# Software Architecture and Design Document

Project ID 35 · UE24CS341A · Team Sentinel Squad

| | |
|---|---|
| System | FSDIRAS — Financial Scam Detection, Investigation and Recovery Assistance System |
| Requirements baseline | SRS v1.0, REQ-1 to REQ-25 |
| Document version | 1.0, 19 November 2026 |
| Companion documents | `uml/` (six UML diagrams), `design-diagrams.md` (ER and sequence), `traceability-matrix.md`, `test-plan.md` |
| Status | Describes the system as built and committed. Every file path and figure below was taken from the code, not from an intention. |

---

## 1. Purpose and audience

The SRS says *what* the system must do. This document says *how* the code is
arranged so that it does it, and — more usefully in a review — **why it is
arranged that way rather than the obvious alternative**. Section 10 is the part
to read if you only read one: it records the thirteen decisions that shaped the
code, each with the alternative that was rejected and the reason.

The audience is a reviewer who has the repository open, a team member joining
mid-project, and the examiner at the viva.

---

## 2. Architectural drivers

Architecture is the set of decisions that are expensive to reverse. Those
decisions were driven by the following, in this order of influence.

| # | Driver | Source | Architectural response | Where it lives |
|---|---|---|---|---|
| D1 | Evidence must be defensible in a legal process; nobody may rewrite history | REQ-11, REQ-13 | Hash-chained, append-only custody log; evidence is archived, never deleted | `services/custody.py`, `models/evidence.py` |
| D2 | A risk score must be explainable, not just produced | REQ-6, SRS 5.1.2 | Linear model over TF-IDF; each contributing term is reported as a reason | `ml/train.py`, `ml/app/main.py` |
| D3 | A score within 5 s for 95% of requests | REQ-2 | Model loaded once at service start-up; 2.5 s client timeout; pooled HTTP client | `ml/app/main.py`, `services/ml_client.py` |
| D4 | Third-party unavailability must degrade features, not break the system | SRS 2.6 | Model service failure falls back to the rule engine; notifications are persisted before dispatch | `services/ml_client.py`, `services/notifications.py` |
| D5 | The model must be replaceable and retrainable without touching the app | SRS 3.2, REQ-7 | The model is a **separate process** behind an HTTP contract, not an import | `ml/` service, `services/ml_client.py` |
| D6 | Four user classes with strictly different authority | SRS 2.3, 6.3 | Role dependency at the route boundary; admin is never implicitly granted | `api/deps.py` |
| D7 | 500 concurrent users, pages under 3 s | SRS 6.1 | Every list endpoint is windowed with a hard ceiling of 500 rows | `api/pagination.py` |
| D8 | Data at rest must not be readable if the disk is taken | SRS 3.3, 6.3 | Evidence encrypted with AES-256-GCM before it touches the disk | `services/storage.py` |
| D9 | The schema must be able to change after the first deployment | — (learned in Sprint 2) | Alembic migrations, run automatically at start-up | `app/db/migrations.py`, `alembic/` |

---

## 3. Context view

Who and what the system talks to. Everything inside the box is ours; everything
outside it is a dependency we do not control.

```
             victim        investigator     recovery officer      admin        guest
                |                |                 |                |            |
                +--------+-------+--------+--------+--------+-------+------------+
                                          |
                                   HTTPS (browser)
                                          |
          ..........................................................................
          :                        F S D I R A S                                   :
          :                                                                         :
          :   React SPA  ---- /api/v1/* ---->  FastAPI application                  :
          :                                      |         |                        :
          :                                      |         +---- model service      :
          :                                      |                 (HTTP, ours)     :
          :                                      v                                  :
          :                               PostgreSQL + encrypted evidence store     :
          :........................................................................:
                                          |
                        +-----------------+------------------+
                        |                                    |
                e-mail / SMS gateway                 (out of scope v1)
                 (third party, SRS 2.6)              bank & police APIs
```

Two external facts shape the design more than anything else on this diagram:
the **gateway is unreliable**, so a notification is a database row first and a
message second; and **bank/police integration is out of scope for v1**, so the
system's output for them is a printable PDF rather than an API call.

---

## 4. Logical view — layers

Four layers, with a one-way dependency rule: **a layer may call the layer below
it and never the one above.** The rule is what keeps business logic testable
without a browser and the database swappable without rewriting rules.

```
   +-------------------------------------------------------------+
   |  Presentation      frontend/src/pages/*.tsx                 |   React 18 + TS
   |                    one API module: frontend/src/api.ts      |
   +-------------------------------------------------------------+
                      | HTTP, JSON, Bearer token
   +-------------------------------------------------------------+
   |  API boundary      backend/app/api/v1/*.py   (7 routers)    |   FastAPI
   |                    deps.py  -> who are you, what may you do |
   |                    pagination.py -> how much may you ask for|
   +-------------------------------------------------------------+
                      | plain Python calls, a Session passed in
   +-------------------------------------------------------------+
   |  Domain services   backend/app/services/*.py  (10 modules)  |
   |                    detection, custody, storage, assignment, |
   |                    notifications, reports_pdf, audit, refs, |
   |                    throttle, ml_client                      |
   +-------------------------------------------------------------+
                      | SQLAlchemy 2.0 ORM
   +-------------------------------------------------------------+
   |  Data              backend/app/models/*.py  (15 tables)     |
   |                    db/session.py, db/migrations.py, alembic/|
   +-------------------------------------------------------------+
```

| Layer | Directory | Holds | Must not |
|---|---|---|---|
| Presentation | `frontend/src/` | 9 routed screens, token storage, error flattening | Contain business rules or trust its own role check for security |
| API boundary | `backend/app/api/` | Request/response schemas, authentication, authorisation, paging, HTTP status | Contain domain logic; a router that computes something is a bug |
| Domain services | `backend/app/services/` | All rules: scoring, custody hashing, encryption, allocation, PDF layout, notification policy | Know about HTTP, `Request`, or FastAPI at all |
| Data | `backend/app/models/`, `alembic/` | Tables, constraints, relationships, schema history | Contain rules that must be enforced even when the DB is bypassed |

The clean test of whether the rule holds: the service layer imports nothing
from `fastapi`, and `test_custody.py` and `test_detection.py` exercise domain
rules with no HTTP client at all.

---

## 5. Component view

This is the structural companion of `uml/02_component.png`, which draws the same
components with their provided and required interfaces in UML notation.

| Component | Type | Provides | Requires |
|---|---|---|---|
| `fsdiras-web` | React SPA, static files | The nine screens | `/api/v1` over HTTP |
| `auth` router | FastAPI router | register, login, me | `security`, `throttle`, `audit`, users table |
| `reports` router | FastAPI router | analyse, submit, list, read | `detection`, `assignment`, `refs` |
| `cases` router | FastAPI router | queue, detail, status, assign, notes | `assignment`, `audit` |
| `evidence` router | FastAPI router | upload, download, custody, verify, archive | `storage`, `custody`, `audit` |
| `recovery` router | FastAPI router | raise, read, update, two PDFs | `notifications`, `reports_pdf` |
| `education` router | FastAPI router | articles, quizzes, attempts | education tables |
| `admin` router | FastAPI router | users, roles, blacklist, analytics, model info | `ml_client`, all tables |
| `detection` service | domain module | `analyse()`, `score_text()`, `band_for()` | `ml_client` (optional), blacklist table, detection log |
| `custody` service | domain module | `append_event()`, `verify_chain()` | custody table, SHA-256 |
| `storage` service | domain module | `validate()`, `scan()`, `store()`, `load()` | filesystem, AES-256-GCM key from `SECRET_KEY` |
| `ml_client` | adapter | `predict()`, `info()` — **returns `None` instead of raising** | `fsdiras-ml` over HTTP |
| `fsdiras-ml` | separate FastAPI service | `/predict`, `/info`, `/health` | `model.joblib`, `metrics.json` |

The one component worth singling out is `ml_client`. It is the only place in the
system where an external process is called, and it is written so that **no
failure of that process can propagate as an exception**: connection error,
timeout, non-JSON body, missing field and out-of-range score all return `None`,
and the caller scores with the rule engine instead. Five of the fifteen tests in
`test_ml_integration.py` exist only to hold that property down.

---

## 6. Process and runtime view

Three processes in development, four services in production.

| Process | Port (dev) | Started by | Holds state? |
|---|---|---|---|
| Vite dev server / static SPA | 5173 | `npm run dev` | No — token in `localStorage` |
| FastAPI application | 8000 | `uvicorn app.main:app` | No — all state in the DB; the login throttle is in-process and deliberately so |
| Model service | 8001 | `uvicorn app.main:app` in `ml/` | Loads the model once into memory |
| Database | file (dev) / 5432 (prod) | SQLite file or PostgreSQL | Yes, all of it |

### 6.1 Start-up sequence of the API

Ordering here is a design decision, not an accident (`app/main.py`):

1. `enforce_production_safety()` — refuses to start on an unsafe production
   configuration, **before** anything touches the database. A deployment with a
   forgeable signing key stops here rather than coming up looking healthy.
2. `run_migrations()` — `alembic upgrade head`. A fresh database gets the full
   schema; an existing one gets only what it is missing.
3. Routers mount; the service accepts traffic.

### 6.2 Critical scenario — "check this message" (REQ-1 to REQ-6)

```
 SPA  --POST /api/v1/detection/analyse-->  reports router
                                              |
                                              v
                                        detection.analyse()
                      1. extract URL / phone / UPI from the text
                      2. blacklist lookup  ------- hit? -> score 100, stop here
                      3. ml_client.predict() ----- None? -> rule engine instead
                      4. band_for(score)  (>=70 high, >=40 medium, else low)
                      5. write a detection_log row            <-- REQ-6
                                              |
 SPA  <--- score, band, reasons, advisory notice, model version
```

Three tiers in descending order of authority: a blacklist entry is a recorded
fact, a model score is an opinion, and the rule engine is a transparent
fallback. That ordering is why a blacklist hit never calls the model.

### 6.3 Critical scenario — filing a report (REQ-5, REQ-8, REQ-9)

Submission runs the same analysis, then opens a case with a generated reference
for **every** report, and auto-assigns to the least-loaded active investigator
when the risk is High. A Low-risk report still gets a case; it simply waits for
a human. See §10, ADR-13 for why.

---

## 7. Data view

Fifteen tables. The full generated reference — every table, every column, with
the requirement each supports — is `design-diagrams.md` sections 2 to 4, which
is produced *from the models themselves* so it cannot drift.

| Area | Tables |
|---|---|
| Identity | `users`, `audit_logs` |
| Detection | `detection_logs`, `blacklist_entries` |
| Investigation | `scam_reports`, `cases`, `case_notes` |
| Evidence | `evidence`, `custody_events` |
| Recovery | `recovery_requests`, `notifications` |
| Education | `awareness_content`, `quizzes`, `quiz_questions`, `quiz_attempts` |

### 7.1 The one structure that is not an ordinary table

`custody_events` is a hash chain. Each row stores the digest of the previous
row, so the rows are ordered by cryptography rather than by trust:

```
  entry_hash(n) = SHA-256( previous_hash | evidence_id | action | actor_id
                           | canonical_timestamp | detail )
  previous_hash(0) = GENESIS
```

Consequences, which are the point of doing it this way:

* Editing any historical row changes its digest, so every later link fails to
  verify. `verify_chain()` returns the id of the first broken link.
* Deleting a row breaks the chain at the join.
* Forging one row's hash is not enough — the next row commits to the old value.

Timestamps are normalised through `canonical_ts()` before hashing, because
SQLite and PostgreSQL disagree about timezone round-tripping and a hash must not
depend on which database you deployed to. `test_custody.py` holds all of this
down with eight tests, including tamper, delete and forge attempts.

---

## 8. Deployment view

| | Development | Production (`render.yaml`) |
|---|---|---|
| SPA | Vite dev server, 5173 | Static site, built with `npm ci && npm run build` |
| API | uvicorn, 8000 | Docker service from `backend/Dockerfile` |
| Model | uvicorn, 8001 | Docker service from `ml/Dockerfile` |
| Database | SQLite file `backend/fsdiras.db` | Managed PostgreSQL |
| Secret | development default (and the app says so, loudly) | generated by the platform, never in the repository |
| Schema | Alembic at start-up | Alembic at start-up — identical path |
| Browser → API | different origin, CORS allows `localhost:5173` | **same origin**: the static site rewrites `/api/*` to the API host |

The production rewrite is deliberate: with the SPA and the API on one origin
there is no CORS configuration to get wrong, and no API URL baked into the
JavaScript bundle. The rewrite must be ordered **before** the SPA catch-all, or
every API call would be answered with `index.html`.

Full walkthrough and the free-tier caveats: `deployment.md`.

---

## 9. Cross-cutting concerns

| Concern | Mechanism | Single place it lives |
|---|---|---|
| Authentication | JWT HS256, 8-hour expiry, bcrypt password hashes | `core/security.py` |
| Authorisation | `require_roles(...)` dependency at the route; admin never implicit | `api/deps.py` |
| Brute-force defence | 10 failures per address, 300 s lockout, in-process | `services/throttle.py` |
| Audit trail | logins, evidence access, status changes (SRS 6.3) | `services/audit.py` |
| Paging | default 100 rows, hard ceiling 500 | `api/pagination.py` |
| Uploads | 10 MB limit, five allowed content types, EICAR-detecting scan hook | `services/storage.py` |
| Encryption at rest | AES-256-GCM, key derived from `SECRET_KEY`; tampering fails to decrypt rather than returning garbage | `services/storage.py` |
| Human-facing identifiers | `PREFIX + YYMM + 5 random base32`, 12 chars (Appendix B) | `services/refs.py` |
| Configuration | pydantic-settings, `.env`, environment overrides | `core/config.py` |
| Schema evolution | Alembic, single head, `alembic check` enforced by a test | `app/db/migrations.py` |
| Error surface | FastAPI validation errors flattened to a sentence for the UI | `frontend/src/api.ts` |

---

## 10. Architecture decision records

Each entry is a decision that would be expensive to reverse, the alternative
that was rejected, and where the decision is enforced in code.

### ADR-1 — The model is a separate service, not a library import
**Context.** SRS 3.2 requires the detection model to be independently
replaceable and retrainable (REQ-7). **Decision.** Run it as its own FastAPI
process and call it over HTTP. **Rejected.** Importing scikit-learn into the API
— simpler, but then retraining means redeploying the whole application, and the
API's memory footprint carries the model whether or not anyone scores a message.
**Consequence.** A network boundary we must defend, which is ADR-2's job.
**Enforced in.** `ml/`, `services/ml_client.py`.

### ADR-2 — A model outage degrades the score, never the service
**Context.** The model process can be down, loading, redeployed or crashed.
**Decision.** `ml_client.predict()` returns `None` on *any* failure and
`detection.analyse()` scores with the built-in rule engine instead, recording
which path was used. **Rejected.** Propagating a 503 — correct-looking, but it
would stop a victim filing a report, and a slightly worse score is recoverable
while a report that could not be filed is not. **Enforced in.**
`test_ml_integration.py` (fallback, timeout, bad body, bad score, missing field).

### ADR-3 — The blacklist is consulted before the model
**Context.** REQ-4 and the two-stage design in SRS 5.1.2. **Decision.** A
blacklist hit short-circuits to 100 and never calls the model. **Rationale.** A
recorded fraudulent UPI ID is a fact; a model score is an opinion, and a fact
outranks an opinion. **Enforced in.** `test_detection.py::test_blacklist_short_circuits_the_model`, `test_ml_integration.py::test_blacklist_still_outranks_the_model`.

### ADR-4 — Chain of custody is a hash chain, not an audit table
**Context.** REQ-11 requires immutability that survives legal scrutiny.
**Decision.** Append-only log where each row commits to the previous row's
digest. **Rejected.** An ordinary table plus "don't update it" as a convention,
or an ORM-level guard — both are one `UPDATE` away from being rewritten, and
nothing about the table would reveal that it had been. **Consequence.** Field
order in the digest is part of the on-disk format and can never be reordered.
**Enforced in.** `services/custody.py`, `test_custody.py` (8 tests).

### ADR-5 — Evidence is archived, never deleted
**Context.** REQ-13. **Decision.** No delete endpoint exists; archiving requires
a reason, and archived evidence remains in the chain. **Rejected.** A soft-delete
flag that hides rows — indistinguishable from deletion to anyone reading the UI,
and it invites a later "clean up old evidence" job. **Enforced in.**
`test_evidence.py::test_evidence_cannot_be_deleted_only_archived`.

### ADR-6 — A linear model over TF-IDF, not a stronger classifier
**Context.** SRS 5.1.2 requires the score be shown with a brief explanation.
**Decision.** TF-IDF (word 1–2 grams plus character 3–5 grams) into logistic
regression. **Rationale.** It is the only common family whose prediction can be
decomposed exactly: each term's contribution is its feature value times its
coefficient, and the contributions sum to the score, so the "reasons" shown to
the user are the actual arithmetic rather than a plausible story. **Rejected.**
Gradient boosting or a transformer — better F1, and no honest explanation.
**Measured cost of the choice.** F1 0.971, ROC-AUC 0.9994 on held-out data; the
accuracy was not the constraint.

### ADR-7 — The 0–100 score is anchored to the model's own decision threshold
**Context.** The model's operating threshold is probability 0.1703; the
application calls 70+ "High". **Decision.** Map probability to score so that the
threshold lands exactly on 70. **Rationale.** Without the anchor, the system
could flag a message as a scam while scoring it 45 — indefensible in a review
and incoherent for a user. **Enforced in.**
`ml/tests/test_service.py::test_threshold_maps_exactly_to_the_high_band`.

### ADR-8 — Notifications are persisted first, dispatched second
**Context.** SRS 2.6 names the e-mail/SMS gateway as a third-party dependency
whose unavailability must not take down core functionality. **Decision.** Write
the notification row inside the caller's transaction, then attempt dispatch and
swallow failures. **Consequence.** A dead gateway leaves a queued, auditable
notification rather than a lost one; the stored row is the source of truth.
**Enforced in.** `services/notifications.py`, `test_recovery.py::test_victim_is_notified_of_status_changes`.

### ADR-9 — Case references are random, not sequential
**Context.** Appendix B specifies 12 alphanumeric characters. **Decision.**
`PREFIX + YYMM + 5 random base32`. **Rationale.** A sequential id leaks how many
reports the system has received, and two reports in the same second can collide.
**Enforced in.** `services/refs.py`, `test_reports_and_cases.py::test_report_references_are_unique`.

### ADR-10 — Evidence is encrypted with an authenticated cipher
**Context.** SRS 3.3, 6.3. **Decision.** AES-256-GCM before the bytes touch the
disk; the stored SHA-256 is of the **plaintext**, so it stays comparable to a
hash computed by the submitter or a court. **Rationale for GCM specifically.**
It is authenticated, so a tampered ciphertext fails to decrypt instead of
quietly returning corrupted bytes — the right failure mode for material that may
become legal evidence. **Enforced in.** `test_evidence.py::test_upload_is_encrypted_at_rest`, `test_verify_detects_a_swapped_file`.

### ADR-11 — Alembic migrations replaced `create_all`
**Context.** `Base.metadata.create_all()` creates missing tables and **cannot
alter an existing one**, so it is not a migration path: the first production
column change would have had no mechanism behind it. **Decision.** Alembic, with
`upgrade head` run automatically at API start-up, and a database that has tables
but no revision is stamped rather than re-created. **Consequence.** A schema
change ships with the deploy that needs it. **Enforced in.** `test_migrations.py`
(4 tests, including `alembic check` for model/migration drift).

### ADR-12 — "Round robin" means least-loaded, not a rotating pointer
**Context.** REQ-9. **Decision.** Assign to the active investigator holding the
fewest open cases. **Rationale.** A rotating pointer keeps handing work to
someone already buried, and resets badly when investigators are added or
deactivated mid-term. **Enforced in.** `services/assignment.py`,
`test_reports_and_cases.py::test_round_robin_spreads_load`.

### ADR-13 — A case is opened for every report, not only High-risk ones
**Context.** REQ-5 creates a case on High risk; REQ-8 requires a Case ID for
every report. Taken literally, a Low-risk report would have no reference to
quote. **Decision.** Open a case for every report; auto-assign only on High
risk. **Status.** Raised in the Sprint 1 retrospective, decided in writing, and
recorded here because it is a deliberate reading of a contradictory
specification rather than an implementation detail. **Enforced in.**
`test_reports_and_cases.py::test_every_report_gets_a_case_reference`,
`test_low_risk_case_waits_for_a_human`.

---

## 11. Quality attributes and how each is verified

| Attribute | Target | Architectural means | Verified by |
|---|---|---|---|
| Performance | score in < 5 s (REQ-2) | model loaded once; 2.5 s client timeout; pooled client | `test_prediction_is_well_inside_the_latency_budget` |
| Availability | third-party failure degrades, not breaks (SRS 2.6) | `None`-returning adapter; persisted notifications | `test_falls_back_to_rules_when_the_service_is_down` |
| Integrity | evidence provably untampered (REQ-11/13) | hash chain; archive-only | `test_custody.py`, `test_evidence.py` |
| Confidentiality | stored files unreadable off-host (SRS 3.3) | AES-256-GCM at rest | `test_upload_is_encrypted_at_rest` |
| Security of access | four role classes (SRS 6.3) | role dependency at the boundary; throttled login | `test_auth.py`, `test_admin_routes_are_closed_to_everyone_else` |
| Scalability | 500 concurrent users (SRS 6.1) | windowed lists, hard 500-row ceiling | `test_report_list_is_windowed` (load figure itself unverified) |
| Explainability | score shown with reasons (SRS 5.1.2) | linear model; coefficient-based reasons | `ml/tests/test_explanations.py` |
| Maintainability | schema can change post-deploy | Alembic single head + drift check | `test_head_has_no_pending_model_changes` |
| Safety of deployment | no unsafe production boot | start-up guard before DB access | `test_production_refuses_to_start_when_unsafe` |

---

## 12. Known limitations and technical debt

Stated here rather than discovered in a review:

1. **The 500-user figure is unverified.** Windowing removes the unbounded
   query, which was the structural problem; no load test has been run.
2. **The login throttle is in-process.** Correct for one API instance, and it
   resets on restart. A second instance needs it moved to the database or Redis.
3. **The malware scan is a hook, not a scanner.** It has a real interface and
   detects the EICAR test string; it is not ClamAV.
4. **Notification dispatch is logged, not sent.** The gateway integration point
   exists; no SendGrid/Twilio credentials are wired.
5. **Half the training data is synthetic.** Live accuracy will be below the
   measured 0.971 F1. `metrics.json` states this in the artefact itself.
6. **No multilingual detection.** The SRS places it out of scope for v1.
7. **Bank and police integration is a PDF**, by scope decision, not an API.

---

## 13. Traceability

Requirement → design → code → test, for all 25 requirements, is
`traceability-matrix.md`. The UML views are in `uml/`, the generated ER and
sequence detail in `design-diagrams.md`, and the verification result in
`test-report.md`.
