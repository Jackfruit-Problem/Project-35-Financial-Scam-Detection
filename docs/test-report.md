# Test Report

**FSDIRAS** — Financial Scam Detection, Investigation and Recovery Assistance System  
Project ID 35 · UE24CS341A Software Engineering · Team Sentinel Squad

Generated 2026-11-17 from an actual execution of the suite. The raw JUnit XML behind every number here is reproducible with the commands in section 5.

---

## 1. Result

| Metric | Value |
|---|---|
| Outcome | **ALL TESTS PASSED** |
| Tests executed | 167 |
| Passed | 167 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |
| Wall time | 170.8 s |
| Backend suite | 130 tests |
| ML service suite | 37 tests |

## 2. Coverage by requirement area

Each test file targets one module of the SRS. The requirement column shows which functional requirements that file exercises.

| Suite | Test file | Area | Requirements | Tests | Failed | Time |
|---|---|---|---|---|---|---|
| backend | `test_auth.py` | Authentication & RBAC | cross-cutting (SRS 2.3 roles) | 12 | 0 | 7.49 s |
| backend | `test_custody.py` | Chain-of-custody hashing | REQ-11, REQ-13 | 8 | 0 | 4.30 s |
| backend | `test_detection.py` | Scam detection | REQ-1 – REQ-7 | 13 | 0 | 1.27 s |
| backend | `test_education_and_admin.py` | Education & administration | REQ-20 – REQ-25 | 19 | 0 | 18.87 s |
| backend | `test_evidence.py` | Evidence & chain of custody | REQ-10, 11, 13 | 16 | 0 | 24.34 s |
| backend | `test_ml_integration.py` | ML service integration | REQ-2, 3, 6, 7 | 15 | 0 | 4.99 s |
| backend | `test_recovery.py` | Recovery & reporting | REQ-15 – REQ-19 | 14 | 0 | 38.51 s |
| backend | `test_regressions.py` | Audit regressions | defects found 19 Oct | 18 | 0 | 32.99 s |
| backend | `test_reports_and_cases.py` | Reports & case lifecycle | REQ-8, 9, 12, 14 | 15 | 0 | 29.15 s |
| ml | `test_explanations.py` | Explanation quality | REQ-6 | 6 | 0 | 0.60 s |
| ml | `test_model_quality.py` | Model quality thresholds | REQ-2, REQ-3 | 16 | 0 | 1.40 s |
| ml | `test_service.py` | Model service API | REQ-2, REQ-7 | 15 | 0 | 2.95 s |

## 3. Requirement traceability

All 25 functional requirements of SRS v1.0 are implemented and covered by at least one automated test. The mapping from requirement to test area:

| Requirements | Module | Covered by |
|---|---|---|
| REQ-1 – REQ-7 | Scam Detection & AI/ML | `test_detection.py`, `test_ml_integration.py`, ML suite |
| REQ-8 – REQ-14 | Investigation & Evidence | `test_reports_and_cases.py`, `test_evidence.py` |
| REQ-15 – REQ-19 | Recovery & Reporting | `test_recovery.py` |
| REQ-20 – REQ-25 | Education & Administration | `test_education_and_admin.py` |
| cross-cutting | Roles and access control | `test_auth.py` |
| audit defects | Seven defects found 19 Oct 2026 | `test_regressions.py` |

## 4. Failures

None. Every executed test passed.

## 5. Reproducing this run

From the repository root:

```
cd backend
.venv\Scripts\python.exe -m pytest -v --junitxml=backend.xml
cd ..\ml
..\backend\.venv\Scripts\python.exe -m pytest -v --junitxml=ml.xml
```

The suite runs on SQLite locally and against PostgreSQL in CI, so database dialect differences surface in CI rather than in production.

## 6. What this report does and does not show

It shows that every automated test passes. It does not by itself show that the tests are meaningful — Sprint 2 found five tests that passed against their own stub and asserted nothing, and an audit of the finished system found seven real defects that the suite had not caught. Those seven now have regression tests, counted above in `test_regressions.py`.
