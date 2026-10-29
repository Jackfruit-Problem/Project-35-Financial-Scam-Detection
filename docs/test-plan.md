# Test Plan

Project ID 35 · UE24CS341A · Team Sentinel Squad · Version 1.0

| | |
|---|---|
| System under test | FSDIRAS — Financial Scam Detection, Investigation and Recovery Assistance System |
| Requirements baseline | SRS v1.0, REQ-1 to REQ-25 and sections 6.1 to 6.5 |
| Companion document | `FSDIRAS - Test Cases.pdf` — 15 documented cases, prioritised |
| Automated tests | 167 (130 application, 37 model) |
| Current result | 167 of 167 pass; 25 of 25 requirements covered |

---

## 1. Purpose

This plan states what is tested, how, by whom, and on what evidence a build is
judged ready to submit. It is deliberately specific about what is **not**
tested: a plan that implies more coverage than exists is worse than one that
admits its limits, because it moves risk out of sight rather than out of the
system.

## 2. Scope

**In scope.** All twenty-five functional requirements; role-based access
control; the integrity of the evidence chain of custody; the risk-scoring model
and its fallback; the PDF reports; and the configuration checks that guard a
deployment.

**Out of scope, with reasons.** These are listed again in section 9 so they are
hard to miss.

| Excluded | Why |
|---|---|
| Concurrent load (SRS 6.1, 500 users) | Measured against a deployment, not programmed. Nothing is deployed. |
| Uptime (SRS 6.4, 99%) | A property of a deployment over time. |
| Daily backups (SRS 6.2) | An operational procedure, not application behaviour. |
| Email and SMS delivery (SRS 2.6) | No gateway contracted; dispatch is stubbed by design. |
| Multilingual input | SRS section 7 places this out of scope for version 1. |
| Front-end unit tests | The interface is exercised manually; automation stops at the API. |

## 3. Test levels

| Level | What it covers | How |
|---|---|---|
| Unit | Individual functions whose logic is worth isolating: risk banding at threshold boundaries, the custody hash, reference generation, the probability-to-score mapping. | pytest, no database or HTTP |
| Integration | A request through routing, authentication, authorisation, the database and back. This is the bulk of the suite, because most defects in this system live between components rather than inside one. | pytest with FastAPI's TestClient against a per-test in-memory database |
| System | The four modules working as one path: report to score to case to evidence to recovery to PDF. | Running system, all three services, exercised through the browser and `curl` |
| Acceptance | The fifteen prioritised cases in the companion document, each mapped to requirements. | Manual, with the automated test that backs each case named in the case |
| Model quality | Whether the trained classifier is still good enough to ship. | A quality gate on a held-out split, with floors below the measured figures |

The model-quality level exists because a statistical artefact cannot be tested
like a rule. A retrained model that scored worse would otherwise pass every
other test in the suite and ship unnoticed.

## 4. Approach

**Tests are named after the rule they protect.** `test_only_assigned_investigator_changes_status`
is the specification of REQ-12 in executable form. When one fails, the first
question is whether the rule was meant to change — not how to make the test
pass.

**Every test runs on every push.** GitHub Actions runs both suites plus linting;
the application suite runs against **PostgreSQL**, not the SQLite used locally,
because SQLite silently tolerates things PostgreSQL rejects. A green local run
is not evidence on its own.

**The model service is stubbed by default.** Without that, results would differ
depending on whether the model happened to be running on the machine — passing
locally and failing in CI, or the reverse. Tests that exercise the model path
opt in explicitly.

**Negative paths carry equal weight.** Roughly half the suite asserts that
something is *refused*: the wrong role, an impossible amount, a deleted
evidence file, an oversized page, a forged custody hash. A system of this kind
is defined as much by what it declines to do as by what it does.

## 5. Test items and coverage

| Area | Tests | Requirements |
|---|---|---|
| `test_reports_and_cases.py` | 15 | REQ-5, 8, 9, 12, 14 |
| `test_education_and_admin.py` | 19 | REQ-20 to REQ-25 |
| `test_regressions.py` | 18 | Defects D-01 to D-07, SRS 6.1, 6.3 |
| `test_evidence.py` | 16 | REQ-10, 13, SRS 3.3, 6.3 |
| `test_ml_integration.py` | 15 | REQ-2, 6, SRS 2.6 |
| `test_recovery.py` | 14 | REQ-15 to REQ-19 |
| `test_detection.py` | 13 | REQ-1 to REQ-4, 6 |
| `test_auth.py` | 12 | REQ-23, SRS 6.3 |
| `test_custody.py` | 8 | REQ-11 |
| **Application total** | **130** | |
| `ml/test_model_quality.py` | 16 | REQ-2, REQ-7 |
| `ml/test_service.py` | 15 | REQ-1, REQ-2, SRS 3.2 |
| `ml/test_explanations.py` | 6 | SRS 5.1.2 |
| **Model total** | **37** | |
| **Overall** | **167** | 25 of 25 requirements |

Requirement-to-case traceability is in section 5 of the companion test-case
document, which fills the column left as TBD in SRS Appendix C.

## 6. Environment

| Item | Detail |
|---|---|
| Operating system | Windows 11 (development), Ubuntu (CI) |
| Backend | Python 3.11.9, FastAPI, SQLAlchemy 2.0 |
| Front end | React 18, TypeScript, Vite |
| Model service | scikit-learn 1.6, served on port 8001 |
| Database | SQLite locally; **PostgreSQL 16 in CI** |
| Runner | pytest; `ruff` for linting; `tsc --noEmit` for the front end |
| Fixture data | `backend/scripts/seed_demo.py` — repeatable, six accounts, five reports |

To reproduce a full run:

```
cd backend && .venv\Scripts\python.exe -m pytest -v
cd ml      && ..\backend\.venv\Scripts\python.exe -m pytest -v
```

Reset the demonstration data before any system-level testing by deleting
`backend/fsdiras.db` and running the launcher, which rebuilds it. Testing
against data left half-edited by earlier practice is the most common way a
demonstration goes wrong.

## 7. Entry and exit criteria

**Entry.** The requirement is implemented, its tests are written, and the suite
runs locally.

**Exit — all five must hold before a build is submitted or demonstrated.**

1. Every automated test passes, in CI, against PostgreSQL.
2. Linting and the front-end type check are clean.
3. Every High-priority acceptance case passes.
4. No open defect of High severity.
5. Every requirement maps to at least one passing case.

All five currently hold at commit `627829d`.

## 8. Defect management

| Severity | Definition | Response |
|---|---|---|
| High | Loses money, loses evidence, or exposes one person's case to another. | Fix before anything else; add a test that fails without the fix. |
| Medium | Produces wrong information or blocks a workflow; nothing lost, nothing leaked. | Fix within the sprint. |
| Low | Inconvenience, robustness gap, or cosmetic. | Fix when touching that area. |

Seven defects were found by auditing the completed system against the
requirements. All seven were reachable through the running application, none
had been caught by the existing suite, and each was fixed with a test that
fails without the fix. They are recorded in section 6 of the test-case
document. Four were High severity:

- Evidence files were addressed relative to the working directory.
- Recovery could never be recorded when no loss had been stated.
- A case could be assigned to a deactivated investigator.
- Nothing limited repeated password guessing.

**The useful finding is not the seven defects. It is that a suite of 130
passing tests had missed all of them**, because they were all written from the
same reading of the requirements as the code. The audit deliberately read the
SRS for things the code could get wrong, rather than re-checking what the code
already claimed to do.

## 9. Risks and limitations

| Risk | Assessment |
|---|---|
| Model accuracy is overstated | Half the training data is synthetic and templated. Figures are therefore reported **per source**: precision 0.921 on real messages against 0.985 on synthetic. The honest figure is the first. |
| No load testing | SRS 6.1 asks for 500 concurrent users. List endpoints are now windowed, which removes the unbounded query, but the figure itself remains unverified. |
| Front end untested automatically | Interface behaviour is verified manually and recorded in the Actual Result column of each case. A regression in the browser would not be caught by CI. |
| Single-process throttling | Login throttling is held in memory. With more than one worker the effective limit multiplies. Documented in the module; a real deployment needs shared state. |
| Interim schema creation | Tables are created on first run rather than by migration. Acceptable for a demonstration; a deployment needs Alembic before any schema change. |

## 10. Responsibilities

Testing follows the module ownership agreed in the SRS. Each owner maintains
the tests for their own requirements; anyone changing shared code is
responsible for the whole suite staying green.

| Member | Module | Requirements |
|---|---|---|
| Zaid Mallik | Scam Detection and AI/ML | REQ-1 to REQ-7 |
| Meha Mahajan | Investigation and Evidence Management | REQ-8 to REQ-14 |
| Mohammed Muaz Iqubal | Recovery and Reporting Assistance | REQ-15 to REQ-19 |
| Masti Choraria | Education, Prevention and Administration | REQ-20 to REQ-25 |
| Shared | Accounts, roles and access control | SRS 2.3, 6.3 |

## 11. Deliverables

| Deliverable | Where |
|---|---|
| This plan | `docs/test-plan.md` |
| Test cases, prioritised, with results | `FSDIRAS - Test Cases.pdf` |
| Automated suites | `backend/tests/`, `ml/tests/` |
| Continuous integration results | GitHub Actions, per push |
| Requirement traceability | Test-case document, section 5 |
| Defect record | Test-case document, section 6 |
