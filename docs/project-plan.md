# Project Plan

**FSDIRAS** — Financial Scam Detection, Investigation and Recovery Assistance System
Project ID 35 · UE24CS341A Software Engineering · Team Sentinel Squad

> The course schedule sheet fixes the deliverable *order* (D-1 to D-6 and the final
> report) but carries no calendar dates, so the planned column below records the
> deliverable sequence and the actual column records the dates taken from this
> repository's git history. Effort is derived from the delivered artifacts, since
> the team did not time-track; replace it if you keep your own records.

---

## 1. Purpose and scope

FSDIRAS lets a member of the public check whether a message is a scam, report one
if they have been defrauded, and follow the resulting case through investigation
and attempted fund recovery. Administrators manage users, the blacklist and the
awareness content, and see analytics across the system.

The scope is the 25 functional requirements of SRS v1.0, REQ-1 to REQ-25. All 25
are implemented. Out of scope for this delivery: live bank APIs (recovery is
recorded, not executed), mobile native apps, and production deployment.

## 2. Team and work breakdown

| Member | Module | Requirements | Delivered |
|---|---|---|---|
| Zaid Mallik | Scam Detection & AI/ML | REQ-1 – REQ-7 | Two-stage detection, blacklist pre-check, TF-IDF + logistic-regression service |
| Meha Mahajan | Investigation & Evidence Management | REQ-8 – REQ-14 | Case lifecycle, allocation, evidence upload, hash-chained chain of custody |
| **Mohammed Muaz Iqubal** | **Recovery & Reporting Assistance** | **REQ-15 – REQ-19** | **Recovery requests, status tracking, PDF reports, victim notifications** |
| Masti Choraria | Education, Prevention & Administration | REQ-20 – REQ-25 | Awareness articles, scored quizzes, user/role admin, blacklist admin, analytics |

Roles: the team runs without a dedicated manager; the module owner is the
decision-maker for their requirements, and interface changes between modules are
agreed in the pull request that makes them.

## 3. Process model

Agile with fixed-length sprints and a retrospective at the end of each. Scrum was
chosen over waterfall because the SRS fixes *what* to build but the detection
accuracy target could only be settled by experiment — the threshold ended up at
0.17, not the obvious 0.5, and that was not knowable in advance.

Work is tracked on a Jira backlog (`docs/jira_backlog.docx`); every functional
requirement maps to at least one backlog item and at least one test case.

## 4. Schedule and milestones

Actual dates below are read from the git history of this repository.

| Milestone | Deliverable | Planned | Actual |
|---|---|---|---|
| D-1 | SRS v1.0, Jira backlog started | Unit-2, Level-3 | 6 Sep 2026 |
| Sprint 1 | All four modules implemented, React front end | Unit-2 | 6 – 7 Sep 2026 |
| D-2 | Test Plan, complete Jira backlog | Unit-2, Level-3 | 27 Sep 2026 |
| D-3 | Software Architecture document | Unit-2, after Lab 3 | 27 Sep 2026 |
| Sprint 2 | ML service, hardening, no-terminal launchers | Unit-3 | 28 Sep – 29 Oct 2026 |
| D-4 | Software Design document + design diagrams | Unit-3, after Lab 4 | 29 Oct 2026 |
| D-5 | Sprint 1 complete, retrospective held | Unit-3, Level-3 | see `retrospective-sprint-1.md` |
| D-6 | Sprint 2 complete, retrospective held | Unit-4, Level-3 | see `retrospective-sprint-2.md` |
| D-7 | UML design diagrams | Unit-4 | 17 Nov 2026 |
| Final | All test reports available | Classes 53-56 | see `test-report.md` |

## 5. Effort

Effort was not time-tracked, so the person-hours below are estimated from the
delivered artifacts rather than read from timesheets. They are stated as estimates
and should be replaced if the team keeps its own figures.

| Area | Evidence of size | Est. person-hours |
|---|---|---|
| Backend | 15 tables, 40 API endpoints, 4 modules | 60 |
| Detection model | TF-IDF + logistic regression, 2 data sources, measured P 0.950 / R 0.993 / AUC 0.9994 | 25 |
| Front end | React + TypeScript + Vite, 9 screens | 35 |
| Tests | 167 automated tests across backend and ML | 30 |
| Audit and defect fixing | 7 defects found and fixed, each with a regression test | 12 |
| Tooling and launchers | double-click run/stop, CI workflow | 8 |
| Documents | SRS, Test Plan, Architecture, Design + 6 UML diagrams, Test Report, 2 retrospectives | 30 |
| **Total** | | **200** |

Spread across four members over roughly eleven weeks, that is about 4.5 hours per
person per week.

## 6. Tools and environment

| Purpose | Tool |
|---|---|
| Version control | Git, GitHub (`Jackfruit-Problem/Project-35-Financial-Scam-Detection`) |
| Backlog | Jira |
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| Database | PostgreSQL in CI, SQLite locally |
| ML | scikit-learn, served by its own FastAPI process on port 8001 |
| Front end | React 19, TypeScript, Vite |
| Test | pytest, GitHub Actions |

## 7. Risk register

| # | Risk | Impact | Response | State |
|---|---|---|---|---|
| R1 | Docker and PostgreSQL not installable on the dev machine (no WSL, no admin rights) | Dialect drift between dev and production | Run on SQLite locally, run CI against real PostgreSQL so drift surfaces | Open, mitigated |
| R2 | Training data for Indian scam patterns is scarce | Model fits foreign SMS spam, not local fraud | UCI SMS corpus plus 1,400 synthetic Indian rows; measure the real-SMS half separately | Closed |
| R3 | Evidence must be defensible as untampered | Fails REQ-11 / REQ-13 | Append-only hash-chained custody log with `verify_chain`, not an ORM rule | Closed |
| R4 | Tests that pass without asserting anything | False confidence | Found in Sprint 2 — five client tests passed against their own stub; `real_ml_client` fixture added | Closed |
| R5 | Single-point knowledge per module | A blocked member blocks a requirement | Module owners documented here; RUNNING.md lets anyone start the system | Open |
| R6 | No deployment yet | Final demo depends on local machines | Launchers make a local run a double-click; deployment config guard already written | Open |

## 8. Configuration management

`main` is the integrated branch and is always runnable. Work happens on feature
branches merged by pull request. The schema is managed by Alembic migrations,
applied automatically when the application starts, so a schema change ships with
the deploy that needs it. The interim `create_all` bootstrap it replaced could
only create missing tables and never alter an existing one.

## 9. Quality plan

Every functional requirement maps to at least one automated test; the suite is the
evidence for the Test Report deliverable. A change is complete when the suite
passes, `ruff` is clean and the front end type-checks. The system is additionally
audited against its own finished state — one such audit in Sprint 2 found seven
real defects that the existing tests had missed, and each now has a regression
test in `backend/tests/test_regressions.py`.

## 10. Pending work

1. ~~Alembic migrations to replace `create_all`~~ — done 17 Nov, with tests
   asserting the migrations build exactly the schema the models declare.
2. Deployment to a public URL — `render.yaml` and `docs/deployment.md` are
   committed; the remaining step is connecting the repository to a hosting
   account, which only an account owner can do.
