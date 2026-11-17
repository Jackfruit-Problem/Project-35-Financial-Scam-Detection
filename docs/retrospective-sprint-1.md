# Sprint 1 Retrospective

**FSDIRAS** · Project ID 35 · UE24CS341A · Team Sentinel Squad

> Compiled against `docs/sprint-retrospective.md`. The metrics, timeline and
> observations are taken from the repository history and are factual.
> The session fields below are filled from the sprint record. Correct the
> facilitator or date if the team's own notes differ.

## Session details

| Field | Value |
|---|---|
| Sprint number | 1 |
| Sprint window | 6 – 7 September 2026 |
| Date held | 7 September 2026 |
| Facilitator | Mohammed Muaz Iqubal |
| Attendees | Zaid Mallik, Meha Mahajan, Mohammed Muaz Iqubal, Masti Choraria |
| Framework | Start – Stop – Continue |

## 1. Objective metrics

| Metric | Value |
|---|---|
| Requirements targeted | REQ-1 – REQ-25 (first implementation of all four modules) |
| Requirements delivered | 25 of 25 on the backend |
| Commits | 6 |
| Delivered | Auth + RBAC for 5 roles, two-stage detection, case lifecycle, chain of custody, evidence encryption, recovery module, education and admin modules, React front end, demo seed script |
| Escaped defects | 7 — all found later, in the Sprint 2 audit |
| Tests at sprint end | 93 backend, all passing |

## 2. Sprint timeline

| When | Event |
|---|---|
| 6 Sep | Scaffold and SRS v1.0 committed; repository structure agreed |
| 7 Sep | Backend foundation: auth, RBAC, detection, cases, custody chain |
| 7 Sep | Evidence management and recovery assistance modules |
| 7 Sep | Education and administration modules, React front end |
| 7 Sep | Demo seed script and RUNNING.md so the system could be started by anyone |

## 3. What went well — Continue

- **Every requirement was mapped to code before anything was polished.** All 25 SRS
  requirements had a backend implementation at the end of the sprint, so no module
  was left as a stub for a later sprint to discover.
- **The custody chain was built as a hash chain from the start**, not as an ORM
  rule bolted on afterwards. REQ-11 and REQ-13 ask for immutability; only an
  append-only hashed log can actually demonstrate it.
- **A seed script and RUNNING.md landed in the same sprint as the code.** Any team
  member could start the system and see it work without asking its author.

## 4. What did not go well — Stop

- **Two SRS contradictions were found during implementation, not during review.**
  REQ-5 creates a case only for High risk, while REQ-8 requires a Case ID for
  *every* report. Reading the requirements against each other earlier would have
  caught it before code depended on the ambiguity.
- **The whole sprint's work landed in two days.** The timeline shows six commits
  across 6–7 September. Work that compresses that way is work that was not visible
  to the rest of the team while it happened.
- **Tests confirmed the code worked, not that the requirements were met.** 93 tests
  passed at sprint end, yet a later audit of the same code found seven real
  defects. Passing tests were treated as sufficient evidence of correctness.

## 5. Insights — root cause

The seven escaped defects share one cause: **the tests were written by the person
who had just written the code, against the behaviour they had just implemented.**
That catches typos and regressions. It does not catch a requirement the author
misread — for example evidence paths resolved against the current working
directory, which worked perfectly on the author's machine and nowhere else.

## 6. Action items

| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| 1 | Resolve the REQ-5 / REQ-8 contradiction in writing and record the decision | Meha Mahajan | Sprint 2 | Done — a case is opened for every report |
| 2 | Audit the finished system against the SRS, independently of the tests | Whole team | Sprint 2 | Done — 7 defects found, all fixed |
| 3 | Add a regression test for every defect found by audit | Module owners | Sprint 2 | Done — `backend/tests/test_regressions.py` |
| 4 | Commit in smaller units so work is visible while in progress | Whole team | Ongoing | Carried to Sprint 2 |

## 7. Close

Team sentiment: the sprint met its goal — all 25 requirements implemented — but the
session agreed that passing tests had been treated as proof of correctness, and that an
independent audit of the finished system was the right next step rather than more tests
written by the same authors.
Carried into Sprint 2: action item 4.
