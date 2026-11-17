# Sprint 2 Retrospective

**FSDIRAS** · Project ID 35 · UE24CS341A · Team Sentinel Squad

> Compiled against `docs/sprint-retrospective.md`. The metrics, timeline and
> observations are taken from the repository history and are factual.
> The session fields below are filled from the sprint record. Correct the
> facilitator or date if the team's own notes differ.

## Session details

| Field | Value |
|---|---|
| Sprint number | 2 |
| Sprint window | 28 September – 29 October 2026 |
| Date held | 29 October 2026 |
| Facilitator | Mohammed Muaz Iqubal |
| Attendees | Zaid Mallik, Meha Mahajan, Mohammed Muaz Iqubal, Masti Choraria |
| Framework | Start – Stop – Continue |

## 1. Objective metrics

| Metric | Sprint 1 | Sprint 2 |
|---|---|---|
| Tests | 93 | 167 (130 backend + 37 ML) |
| Commits | 6 | 7 |
| Escaped defects found | — | 7, all fixed in sprint |
| Detection | rule scorer `rules-v0` | TF-IDF + logistic regression, its own service |
| Model quality | not measured | precision 0.950, recall 0.993, AUC 0.9994 |
| Carried-in actions | — | 3 of 3 closed |

## 2. Sprint timeline

| When | Event |
|---|---|
| 28 Sep | Double-click launchers so the app runs without a terminal |
| 29 Sep | Trained detection model added as its own service on port 8001 |
| 29 Sep | Email addresses accepted regardless of capitalisation |
| 19 Oct | Audit of the finished system — seven defects found and fixed |
| 22 Oct | Launcher waits for the model service before reporting it unavailable |
| 29 Oct | Test plan, design diagrams and the retrospective template added |

## 3. What went well — Continue

- **Every Sprint 1 action item was closed.** The audit happened, the seven defects
  it found were fixed, and each one gained a regression test. Action items from the
  previous retrospective were not allowed to quietly disappear.
- **The audit was worth more than the test suite that sprint.** Seven real defects,
  none of which any existing test caught, including two that made features
  unusable: evidence unreadable unless the server was started from one particular
  folder, and recovery impossible to record when no loss amount was stated.
- **The model was measured honestly rather than reported optimistically.** The
  real-SMS half was scored separately (0.921 / 0.987) instead of hiding behind the
  flattering combined figure, and the decision threshold was set to the lowest
  value holding 95% precision — 0.17, not the default 0.5.
- **The ML model was isolated behind its own HTTP boundary**, with the rule scorer
  kept as a fallback. The detection feature degrades instead of failing when the
  model service is down.

## 4. What did not go well — Stop

- **Five tests were passing vacuously.** An autouse fixture stubbed
  `ml_client.predict`; the tests asserted `None` and received the stub's `None`.
  They had never tested anything. Found only by reading them, not by running them.
- **A performance problem went unnoticed because nothing measured it.** A
  per-request `httpx.post()` cost about 800 ms while the model itself answered in
  17 ms — the cost was client construction. A module-level pooled client brought it
  to roughly 19 ms, a 40× difference that no test would ever have reported.
- **The launcher was reported as working while it was not.** It announced success
  while the new servers had failed to bind, because the health check was being
  answered by the *old* process still holding the port.
- **Graded documents were left to the end of the sprint.** The test plan and design
  diagrams both landed on 29 October, the last day. Documents written at the
  deadline describe what was built rather than guiding what gets built.

## 5. Insights — root cause

Sprint 1's lesson was that passing tests are not proof of correctness. Sprint 2
sharpened it: **a test only means something if it can fail.** The five stubbed
tests, the unmeasured 800 ms, and the launcher confirming its own success against
the wrong process are the same mistake in three places — a check whose outcome did
not depend on the thing it claimed to verify.

The practical rule the team took from it: when adding a check, break the thing it
watches on purpose once, and confirm the check goes red.

## 6. Action items

| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| 1 | Replace the interim `create_all` with Alembic migrations before any deployment | Meha Mahajan | Sprint 3 | Open |
| 2 | Deploy to a public URL so the demo does not depend on a local machine | Zaid Mallik | Sprint 3 | Open |
| 3 | Prove each new test can fail before accepting it | Whole team | Ongoing | Carried to Sprint 3 |
| 4 | Write the graded documents during the sprint, not on its last day | Mohammed Muaz Iqubal | Sprint 3 | In progress — UML diagrams, project plan and test report done 17 Nov |

## 7. Close

Team sentiment: confidence in the system rose over the sprint, but the session's own
conclusion was that the rise came from the audit rather than from the test count. The
team ended on the rule that a check which cannot be made to fail is not yet evidence.
Carried into Sprint 3: action items 1, 2 and 3.
