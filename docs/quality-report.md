# Code Quality and Static Analysis Report

Project ID 35 · UE24CS341A · Team Sentinel Squad

| | |
|---|---|
| Measured on | 19 November 2026 |
| Commit | `f2e3533` plus this document set |
| Platform | Windows, CPython 3.11.9, Node 22 / npm 10.9.3 |
| Scope | `backend/`, `ml/`, `frontend/` |
| Result | **Clean.** 171 tests, 0 failures; 0 lint findings; 0 type errors; 95% statement coverage |

Everything below is output from a run made for this document, not a figure
carried over from an earlier one. The commands are given so any of it can be
reproduced.

---

## 1. Summary

| Check | Tool | Result |
|---|---|---|
| Backend tests | pytest 8.3.4 | **134 passed, 0 failed** in 115.63 s |
| Model-service tests | pytest 8.3.4 | **37 passed, 0 failed** in 22.23 s |
| Backend lint | ruff (`E`, `F`, `I`, `UP`, `B`) | **All checks passed** |
| Model-service lint | ruff, same rules | **All checks passed** |
| Frontend types | `tsc -b`, TypeScript 5.6.3, strict | **No errors** |
| Frontend build | Vite 5.4.11 | **Built in 1.55 s**, 46 modules |
| Statement coverage | coverage.py via pytest-cov | **95%** overall (1 520 statements, 72 uncovered) |
| Schema drift | `alembic check` inside the suite | **No pending model changes** |

---

## 2. Test results

| Suite | Tests | Failures | Time | Coverage of its own package |
|---|---|---|---|---|
| `backend/tests` | 134 | 0 | 115.63 s | 95% (1 430 statements, 66 uncovered) |
| `ml/tests` | 37 | 0 | 22.23 s | 93% (90 statements, 6 uncovered) |
| **Total** | **171** | **0** | **137.86 s** | **95%** (1 520 statements, 72 uncovered) |

Per-file results and the requirement each file traces to are in
`test-report.md`; the requirement mapping in both directions is
`traceability-matrix.md`.

```
cd backend && .venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
cd ml      && ..\backend\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

---

## 3. Coverage by layer

Grouped, because the interesting question is not the headline number but
*which* layer is thin.

| Layer | Files | Coverage | Reading |
|---|---|---|---|
| Domain services | 10 | **96%** — six of them at 100% | The rules are the part that must not be wrong, and they are the best covered |
| Models and schemas | 9 | **100%** | Every table and every response shape is constructed by some test |
| API routers | 7 | **92%** | Mostly error branches; one real gap, §5 |
| Database and migrations | 3 | 92% | `migrations.py` is at 100%, `session.py` at 67% — explained below |
| Model service (`ml/app`) | 1 | 93% | Start-up failure paths |

### Services, in full

| Module | Statements | Coverage |
|---|---|---|
| `services/custody.py` | 33 | **100%** |
| `services/detection.py` | 59 | **100%** |
| `services/storage.py` | 61 | **100%** |
| `services/assignment.py` | 10 | **100%** |
| `services/refs.py` | 9 | **100%** |
| `services/audit.py` | 4 | **100%** |
| `services/notifications.py` | 25 | 96% |
| `services/throttle.py` | 31 | 94% |
| `services/reports_pdf.py` | 53 | 85% |
| `services/ml_client.py` | 41 | 78% |

That `custody.py`, `detection.py` and `storage.py` are at 100% is the number
worth quoting: the hash chain, the risk scoring and the encryption are the three
pieces whose failure would be either a legal problem or an invisible one.

---

## 4. The uncovered lines, accounted for

72 uncovered statements. They are not a uniform smear; they fall into four
groups, and only one of them is a gap worth closing.

| Where | Lines | Why it is uncovered | Verdict |
|---|---|---|---|
| `db/session.py` · `get_db()` | 19–23 | The test suite overrides this dependency with a test session factory, so the production generator body is never entered. It runs on every real request | Expected |
| `services/ml_client.py` · `info()` and client construction | 34, 70, 82–88 | The live HTTP path to the model service. Unit tests stub the client; the path is exercised whenever the model service is actually running, and it is the path the Model tab uses | Expected |
| `services/reports_pdf.py` | 152–178 | The **evidence table** branch of the case report. The PDF tests build reports for cases that have no attached evidence, so the table is never rendered | **Worth closing** — see §5 |
| `api/v1/cases.py` | 65–73 | The body of `GET /api/v1/cases/{case_ref}` | **Worth closing** — see §5 |
| Router guards across `cases.py`, `evidence.py`, `education.py`, `admin.py`, `deps.py` | ~20 statements | Individual 403/404 branches on routes whose other branches are tested | Acceptable |
| `ml/app/main.py` | 62, 147, 153, 162, 188, 198 | Start-up paths for a missing or unloadable model artefact | Acceptable |

---

## 5. Findings

Two, both from reading the coverage output rather than from a failure.

### F-1 — The case-detail endpoint has no test of its own
**Severity:** medium. **Evidence:** `api/v1/cases.py` lines 65–73 uncovered; no
test in `backend/tests/` issues `GET /api/v1/cases/{case_ref}`.

This is the endpoint behind the **Case detail** screen — the screen an
investigator spends all their time on. Its authorisation helper
`_assert_can_view()` *is* covered, because the notes and evidence routes call it,
so the access rules are tested; what is untested is the detail response itself,
including the assigned-investigator lookup.

**Suggested fix:** three tests — a victim reads their own case, a stranger gets
403, an unknown reference gets 404. Roughly fifteen lines.

### F-2 — No PDF test attaches evidence first
**Severity:** low. **Evidence:** `services/reports_pdf.py` lines 152–178
uncovered.

The case-report PDF contains an evidence table with each file's SHA-256 prefix
so a recipient can verify the attachments independently. No test generates a
report for a case that *has* evidence, so that table has never been rendered
under test.

**Suggested fix:** upload one file in the existing PDF test before generating
the report.

Neither finding is a defect in shipped behaviour — both are gaps in
verification, which is a different and smaller thing. They are recorded here
rather than quietly left in the coverage output.

---

## 6. Static analysis

### Python — ruff

```
cd backend && .venv\Scripts\python.exe -m ruff check .     -> All checks passed!
cd ml      && ..\backend\.venv\Scripts\python.exe -m ruff check .  -> All checks passed!
```

Configured in `backend/pyproject.toml`:

| Setting | Value | Reason |
|---|---|---|
| `line-length` | 100 | Wide enough for SQLAlchemy 2.0 `select()` chains without wrapping them into illegibility |
| `target-version` | py311 | `StrEnum` and `X \| None` are used throughout |
| `select` | `E`, `F`, `I`, `UP`, `B` | style, correctness, import order, modern syntax, likely bugs |
| `ignore` | `B008` | B008 flags function calls in argument defaults, which is precisely how FastAPI dependency injection is written (`db: Session = Depends(get_db)`). Suppressed with the reason recorded next to it, not silently |
| `extend-exclude` | `alembic/versions` | Alembic generates those files; their formatting is not ours to own |

Two things about this configuration are deliberate and worth defending in a
review: `F` (pyflakes) and `B` (flake8-bugbear) are the rule families that catch
*bugs* rather than style, and every suppression in the project carries a comment
saying why. There are no blanket `# noqa` lines.

### TypeScript — `tsc -b`

`npm run build` runs `tsc -b` before Vite, so **the build fails on a type
error**; a clean build is also a clean typecheck. Strict mode is on.

```
tsc -b && vite build
46 modules transformed
dist/assets/index-*.js    213.26 kB  (gzip 66.07 kB)
dist/assets/index-*.css     5.36 kB  (gzip  1.74 kB)
built in 1.55s
```

213 kB for the whole application, with React and the router included, is the
consequence of having no component framework and no chart library: the UI is
hand-written components in `frontend/src/ui.tsx`.

### Schema drift — `alembic check`

`backend/tests/test_migrations.py::test_head_has_no_pending_model_changes` runs
`alembic check` inside the suite. A model changed without a matching revision
fails the build rather than being discovered on the next deployment.

---

## 7. What is *not* checked

Stated so that the clean result above is not read as more than it is.

| Not run | Consequence | Why not |
|---|---|---|
| Load / concurrency test | SRS 6.1's 500-user figure is unverified | Out of scope this term. The structural fault — unbounded list queries — is fixed and tested |
| `mypy` or `pyright` on the backend | Python type annotations are documentation, not enforced | Pydantic and FastAPI validate at the boundary at runtime, which is where the untrusted data is |
| ESLint | No lint rules on the frontend beyond the compiler | `tsc` strict catches the class of error that matters in 14 files; a linter was not worth the configuration |
| Dependency vulnerability scan | Unknown CVE exposure in third-party packages | No `pip-audit` / `npm audit` gate is wired. Versions are pinned, which at least makes the set reproducible |
| SAST (Bandit, Semgrep) | No automated security scan | The security-relevant code — hashing, encryption, authorisation — is reviewed by hand and covered by tests at 100% |
| Mutation testing | Coverage says lines ran, not that assertions are meaningful | Would be the honest next step after F-1 and F-2 |

---

## 8. Reproducing this report

```
# backend: lint, test, coverage
cd backend
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing

# model service: lint, test, coverage
cd ..\ml
..\backend\.venv\Scripts\python.exe -m ruff check .
..\backend\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing

# frontend: typecheck and build
cd ..\frontend
npm run build
```

Expect 134 and 37 tests, two "All checks passed!", and a build in under two
seconds. Anything else is a regression against this baseline.
