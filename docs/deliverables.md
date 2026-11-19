# Deliverables Index

Project ID 35 · UE24CS341A · Team Sentinel Squad · FSDIRAS

Every artefact this project has produced, where it is, and what state it is in.
Compiled 19 November 2026. This is the page to open first in a review.

The artefacts live in two places, and the distinction matters:

| Location | What it holds |
|---|---|
| `../docs/` (and `../docs/swe/`) | The documents **submitted to the course** on their deadlines — Word and PDF, frozen as submitted |
| `docs/` in the repository | The repository's **living documents** — Markdown under version control, regenerated from the code, each with a PDF beside it |

Where both exist, the submitted copy is the record of what was handed in and the
repository copy is the current truth about the system.

---

## 1. Course deliverables D-1 to D-7

| ID | Deliverable | Artefact | Date | State |
|---|---|---|---|---|
| D-1 | SRS v1.0 | `SRS_ProjectID35_FSDIRAS.docx` / `.pdf` (repository root) | 6 Sep 2026 | Submitted. 25 functional requirements, REQ-1 to REQ-25 |
| D-1 | Jira backlog started | `../docs/jira_backlog.docx`, `../docs/swe/jira_backlog.pdf` | 27 Sep 2026 | Submitted |
| D-2 | Test Plan | `../docs/35_Project Test Plan.docx`, `../docs/swe/35_Project Test Plan.pdf` (submitted) · `docs/test-plan.md` (living) | 27 Sep 2026 | Both current |
| D-3 | Software Architecture document | `../docs/SweArchitecture.docx`, `../docs/swe/SweArchitecture.pdf` (submitted) · `docs/architecture.md` (living, **new 19 Nov**) | 27 Sep 2026 · 19 Nov 2026 | The repository version is written against the code as built and adds 13 architecture decision records |
| D-4 | Software Design document + design diagrams | `docs/design-diagrams.md` | 29 Oct 2026 | ER sections generated from the live models, so they cannot drift |
| D-5 | Sprint 1 complete + retrospective | `docs/retrospective-sprint-1.md` | — | Held and recorded |
| D-6 | Sprint 2 complete + retrospective | `docs/retrospective-sprint-2.md` | — | Held and recorded |
| D-7 | UML design diagrams | `docs/uml/` — six PNGs + one PDF | 17 Nov 2026 | Proper UML notation, not flowcharts |
| Final | All test reports | `docs/test-report.md` · `../docs/FSDIRAS - Test Cases.pdf` | 19 Nov 2026 | **171 tests, 0 failures** |

---

## 2. Everything in the repository, by purpose

### 2.1 Requirements

| Artefact | Path | Notes |
|---|---|---|
| SRS v1.0 | `SRS_ProjectID35_FSDIRAS.docx` / `.pdf` | The baseline. Its requirements table leaves the last column `TBD` |
| Requirements traceability matrix | `docs/traceability-matrix.md` | **New 19 Nov.** Fills in that column: every requirement → code → interface → named test, and the reverse direction too |

### 2.2 Design

| Artefact | Path | Notes |
|---|---|---|
| Software architecture document | `docs/architecture.md` | **New 19 Nov.** Drivers, four views, cross-cutting concerns, 13 ADRs, known limitations |
| Design diagrams (ER, sequence, deployment) | `docs/design-diagrams.md` | Generated from the SQLAlchemy models by `docs/gen_diagrams.py` |
| UML — use case | `docs/uml/01_usecase.png` | 5 actors, 17 use cases, `«include»` / `«extend»` — Lab 1 |
| UML — component | `docs/uml/02_component.png` | 7 components, ball-and-socket interfaces — Lab 3 |
| UML — class | `docs/uml/03_class.png` | |
| UML — sequence | `docs/uml/04_sequence.png` | |
| UML — state machine | `docs/uml/05_state.png` | Case and recovery lifecycles |
| UML — activity | `docs/uml/06_activity.png` | |
| All six UML diagrams | `docs/uml/FSDIRAS - UML Diagrams.pdf` | One file to hand over |

### 2.3 Planning and process

| Artefact | Path | Notes |
|---|---|---|
| Project plan | `docs/project-plan.md` | Scope, work breakdown by module, process model, schedule, effort estimates, risk register, configuration management, quality plan |
| Sprint 1 retrospective | `docs/retrospective-sprint-1.md` | Includes the REQ-5 / REQ-8 contradiction and how it was resolved |
| Sprint 2 retrospective | `docs/retrospective-sprint-2.md` | Includes the seven defects found by auditing the finished system |
| Retrospective facilitator template | `docs/sprint-retrospective.md` | Reusable checklist, prime directive, ROTI |
| Jira backlog | `../docs/jira_backlog.docx` | Outside the repository, in the course-project folder; PDF in `../docs/swe/` |

### 2.4 Verification

| Artefact | Path | Notes |
|---|---|---|
| Test plan | `docs/test-plan.md` | Levels, approach, entry/exit criteria, defect management, responsibilities |
| Test report | `docs/test-report.md` | Generated from the actual run: 171 tests, 0 failures, per-file timings and requirement mapping |
| Code quality and static analysis report | `docs/quality-report.md` | **New 19 Nov.** ruff, `tsc`, 95% coverage, the uncovered lines accounted for, and two named verification gaps |
| Test cases (submitted) | `../docs/FSDIRAS - Test Cases.pdf` | |

### 2.5 Operation and handover

| Artefact | Path | Notes |
|---|---|---|
| Installation and operations guide | `RUNNING.md` | Set-up, demo data, launchers, migrations, troubleshooting |
| User manual | `docs/user-manual.md` | **New 19 Nov.** All nine screens, by role, with the bands, the limits and the error messages explained |
| Deployment guide | `docs/deployment.md` | Render blueprint walkthrough, production safety guard, free-tier caveats |
| Deployment blueprint | `render.yaml` | Four services; the SPA rewrites `/api/*` to the API host |
| Containers | `backend/Dockerfile`, `ml/Dockerfile`, `docker-compose.yml` | |
| Project README | `README.md` | |
| Team guide (submitted) | `../docs/FSDIRAS - Team Guide.pdf` | |
| Viva preparation | `docs/viva-prep.md` | Software-engineering theory, this project's numbers, and the questions to expect |

---

## 3. PDF set

Every living document has a PDF beside it, in the repository's `docs/`:

| PDF |
|---|
| `FSDIRAS - Software Architecture.pdf` |
| `FSDIRAS - Traceability Matrix.pdf` |
| `FSDIRAS - Design Diagrams.pdf` |
| `FSDIRAS - Project Plan.pdf` |
| `FSDIRAS - Test Plan.pdf` |
| `FSDIRAS - Test Report.pdf` |
| `FSDIRAS - Quality Report.pdf` |
| `FSDIRAS - User Manual.pdf` |
| `FSDIRAS - Installation Guide.pdf` |
| `FSDIRAS - Deployment Guide.pdf` |
| `FSDIRAS - Sprint 1 Retrospective.pdf` |
| `FSDIRAS - Sprint 2 Retrospective.pdf` |
| `FSDIRAS - Retrospective Template.pdf` |
| `FSDIRAS - Deliverables Index.pdf` |
| `FSDIRAS - Viva Prep.pdf` |
| `uml/FSDIRAS - UML Diagrams.pdf` |

The Design Diagrams PDF carries all six Mermaid diagrams rendered as vector
graphics, so the file stands on its own away from GitHub.

---

## 4. The system itself

| | |
|---|---|
| Repository | `jackfruit/`, pushed to `main` |
| Backend | FastAPI + SQLAlchemy 2.0 + Alembic — 15 tables, 40 endpoints under `/api/v1` |
| Model service | Separate FastAPI service — TF-IDF + logistic regression, F1 0.971, ROC-AUC 0.9994 |
| Front end | React 18 + TypeScript + Vite — 9 screens, 213 kB bundle |
| Tests | 171, all passing; 95% statement coverage |
| Lint / types | `ruff` clean on both Python packages; `tsc -b` strict, no errors |
| Launchers | `Run FSDIRAS.bat`, `Stop FSDIRAS.bat` — no terminal needed |

---

## 5. What is still open

Two items, both stated in the documents that own them rather than only here.

| # | Item | Owner document | Why it is open |
|---|---|---|---|
| 1 | Deployment to a public URL | `deployment.md` | The blueprint and the walkthrough are committed. Connecting the repository to a hosting account needs the account owner's own login — about ten minutes |
| 2 | Two verification gaps: the case-detail endpoint and the PDF evidence table have no test of their own | `quality-report.md` §5 | Found by reading the coverage output for this document set. Neither is a defect in behaviour; both are gaps in proof. Roughly twenty lines of test between them |

Nothing else in the requirement baseline is outstanding: 24 of 25 requirements
are implemented and tested, and the one partial — REQ-7, which has no
in-application retrain button — is recorded as a scope decision in
`traceability-matrix.md` §9 rather than counted as done.
