# Requirements Traceability Matrix

Project ID 35 · UE24CS341A · Team Sentinel Squad

| | |
|---|---|
| Baseline | SRS v1.0, REQ-1 to REQ-25 |
| Version | 1.0, 19 November 2026 |
| Verification run | 171 tests, 0 failures (134 backend + 37 model) |
| Companion documents | `architecture.md`, `test-plan.md`, `test-report.md`, `uml/` |

---

## 1. How to read this

The SRS requirements table leaves its last column as `TBD`. This document fills
it in, in both directions:

* **Forward** (§3 – §6): every requirement → the code that implements it → the
  interface it is reached through → the test that proves it.
* **Backward** (§8): every test file → the requirements it covers, so no test
  is an orphan and no requirement rests on nothing.

A test is cited by its real function name, so any claim here can be checked by
running it. Where a parametrised test expands into several cases, the count in
`test-report.md` is higher than the number of names cited here.

## 2. Summary

| | Count |
|---|---|
| Functional requirements in the baseline | 25 |
| Implemented and covered by at least one automated test | 24 |
| Implemented in part, with the gap stated | 1 (REQ-7) |
| Not implemented | 0 |
| Requirements with no test | 0 |

The one partial is REQ-7, and the gap is stated plainly in §3 rather than
rounded up: the administration screen reports the model in service and its
measured metrics, and retraining runs as an offline pipeline (`ml/train.py`).
There is no in-application "retrain now" button.

---

## 3. Scam Detection and AI/ML — REQ-1 to REQ-7

Module owner: Zaid Mallik

| REQ | Requirement | Design element | Interface | Verified by | Status |
|---|---|---|---|---|---|
| REQ-1 | Accept text / URL / transaction input for analysis | `services/detection.py` · `extract_indicators()`, URL/UPI/phone patterns | `POST /api/v1/detection/analyse`, `POST /api/v1/reports`; screen **Check a message** | `test_detection.py::test_analyse_endpoint_returns_score_and_reasons`, `ml/test_service.py::test_predict_returns_the_agreed_shape` | Done |
| REQ-2 | Compute risk score within 5 seconds | Model loaded once at service start-up; `ML_TIMEOUT_SECONDS = 2.5`; pooled HTTP client | `POST /predict` on the model service | `ml/test_service.py::test_prediction_is_well_inside_the_latency_budget`, `test_ml_integration.py::test_model_score_is_used_when_the_service_answers` | Done |
| REQ-3 | Categorise into Low / Medium / High | `services/detection.py` · `band_for()`; thresholds `RISK_MEDIUM_THRESHOLD=40`, `RISK_HIGH_THRESHOLD=70` in `core/config.py` | Returned on every analysis; shown as the band on **Check a message** | `test_detection.py::test_risk_bands_at_boundaries`, `test_score_is_bounded_to_100`, `ml/test_service.py::test_threshold_maps_exactly_to_the_high_band` | Done |
| REQ-4 | Maintain and check a blacklist | `services/detection.py` · `check_blacklist()`; table `blacklist_entries` | Checked on every analysis; managed at `GET/POST/DELETE /api/v1/admin/blacklist` | `test_detection.py::test_blacklist_short_circuits_the_model`, `test_education_and_admin.py::test_blacklisted_value_is_used_by_detection`, `test_ml_integration.py::test_blacklist_still_outranks_the_model` | Done |
| REQ-5 | Auto-create a case on high risk | `api/v1/reports.py` submission path + `services/assignment.py` | `POST /api/v1/reports` | `test_reports_and_cases.py::test_high_risk_auto_creates_and_assigns`, `test_low_risk_case_waits_for_a_human`, `test_ml_integration.py::test_high_model_score_auto_assigns_the_case` | Done — see ADR-13: a case is opened for *every* report, assignment only on High |
| REQ-6 | Log detection requests for audit | `services/detection.py` · `analyse()` writes `detection_logs` (score, band, path taken, model version) | Written server-side on every analysis | `test_detection.py::test_analyse_logs_every_request`, `test_ml_integration.py::test_fallback_is_recorded_in_the_log`, `test_model_version_is_recorded_when_the_model_answers` | Done |
| REQ-7 | Admin-triggered model retraining | Retraining pipeline `ml/build_dataset.py` → `ml/train.py` → `artifacts/model.joblib` + `metrics.json`; `GET /api/v1/admin/model` serves the live artefact's own measured metrics | Admin screen → **Model** tab | `test_ml_integration.py::test_model_screen_shows_measured_metrics`, `test_model_screen_is_admin_only`, `test_model_screen_reports_unavailable_rather_than_failing`, `ml/test_model_quality.py::test_metrics_file_matches_the_shipped_model` | **Partial.** The model in service is visible and its metrics are measured, not copied. Retraining is an offline, reviewed step with a quality gate (`ml/tests`), not a button. Stated as a scope decision, not an oversight. |

---

## 4. Investigation and Evidence Management — REQ-8 to REQ-14

Module owner: Meha Mahajan

| REQ | Requirement | Design element | Interface | Verified by | Status |
|---|---|---|---|---|---|
| REQ-8 | Auto-generate a unique Case ID | `services/refs.py` · `new_case_ref()` — `PREFIX + YYMM + 5 random base32`, 12 chars (Appendix B) | Returned by `POST /api/v1/reports`; shown on **My reports** | `test_reports_and_cases.py::test_every_report_gets_a_case_reference`, `test_report_references_are_unique` | Done |
| REQ-9 | Assign a case to an investigator | `services/assignment.py` · `next_investigator()` — least-loaded active investigator | Automatic on High risk; `POST /api/v1/cases/{case_ref}/assign/{investigator_id}` for manual | `test_reports_and_cases.py::test_round_robin_spreads_load`, `test_admin_can_assign_manually`, `test_non_admin_cannot_assign`, `test_regressions.py::test_a_case_cannot_be_assigned_to_a_deactivated_investigator` | Done |
| REQ-10 | Upload evidence files | `services/storage.py` · `validate()`, `scan()`, `store()`; 10 MB limit, five allowed content types | `POST /api/v1/cases/{case_ref}/evidence`; screen **Case detail** | `test_evidence.py::test_victim_can_upload_to_their_own_case`, `test_oversized_upload_is_rejected`, `test_unsupported_file_type_is_rejected`, `test_malware_scan_blocks_a_known_bad_file`, `test_empty_upload_is_rejected` | Done |
| REQ-11 | Immutable chain-of-custody log | `services/custody.py` · `append_event()`, `compute_entry_hash()`, `verify_chain()`; SHA-256 chain from `GENESIS` | `GET /api/v1/evidence/{id}/custody`, `GET /api/v1/evidence/{id}/verify` | `test_custody.py` — all 8, including `test_editing_a_historical_entry_is_detected`, `test_deleting_a_link_is_detected`, `test_forging_a_hash_without_the_chain_fails`; `test_evidence.py::test_verify_detects_a_swapped_file` | Done |
| REQ-12 | Case status states (exactly five) | `models/enums.py` · `CaseStatus`; transition guarded in `api/v1/cases.py` | `PATCH /api/v1/cases/{case_ref}/status` | `test_reports_and_cases.py::test_status_must_be_one_of_the_five`, `test_only_assigned_investigator_changes_status` | Done |
| REQ-13 | Prevent evidence deletion | No delete route exists; archive requires a reason and keeps the file and the chain | `POST /api/v1/evidence/{id}/archive` | `test_evidence.py::test_evidence_cannot_be_deleted_only_archived`, `test_archiving_requires_a_reason`, `test_victim_cannot_archive_evidence`, `test_archived_evidence_survives_in_the_chain` | Done |
| REQ-14 | Timestamped case notes | `models/report.py` · `CaseNote` (author id + created-at, both server-set) | `POST`/`GET /api/v1/cases/{case_ref}/notes` | `test_reports_and_cases.py::test_notes_are_attributed_and_timestamped` | Done |

---

## 5. Recovery and Reporting Assistance — REQ-15 to REQ-19

Module owner: **Mohammed Muaz Iqubal**

| REQ | Requirement | Design element | Interface | Verified by | Status |
|---|---|---|---|---|---|
| REQ-15 | Auto-populate a recovery request | `api/v1/recovery.py` — fields taken from the case and its report, not re-typed; one request per case enforced | `POST /api/v1/cases/{case_ref}/recovery` | `test_recovery.py::test_recovery_request_is_autopopulated_from_the_case`, `test_only_one_recovery_request_per_case`, `test_victim_cannot_raise_a_recovery_request` | Done |
| REQ-16 | Update recovery status | `models/enums.py` · `RecoveryStatus` (five values); role check restricts the write to a recovery officer | `PATCH /api/v1/cases/{case_ref}/recovery` | `test_recovery.py::test_recovery_status_progresses_through_the_five_values`, `test_invalid_recovery_status_is_rejected`, `test_investigator_cannot_record_a_recovery_outcome` | Done |
| REQ-17 | Generate a downloadable PDF report | `services/reports_pdf.py` · `case_report()`, `recovery_report()` — Appendix B field sets, case reference and the section 7 disclaimer on every page | `GET /api/v1/cases/{case_ref}/report.pdf`, `GET /api/v1/cases/{case_ref}/recovery-report.pdf` | `test_recovery.py::test_case_report_pdf_is_generated`, `test_recovery_report_pdf_is_generated`, `test_recovery_report_requires_a_raised_request`, `test_stranger_cannot_download_a_case_report` | Done |
| REQ-18 | Notify the victim on status change | `services/notifications.py` · `notify_recovery_change()` — row persisted inside the transaction, dispatch attempted after and allowed to fail | Written on every status change; table `notifications` | `test_recovery.py::test_victim_is_notified_of_status_changes`, `test_no_notification_when_nothing_changed` | Done |
| REQ-19 | Track reported versus recovered amount | `models/recovery.py` — `amount_reported`, `amount_recovered`; ceiling enforced server-side | Returned by `GET /api/v1/cases/{case_ref}/recovery`; both PDFs | `test_recovery.py::test_reported_versus_recovered_is_tracked`, `test_recovered_amount_cannot_exceed_the_loss`, `test_regressions.py::test_recovery_can_be_recorded_when_no_amount_was_reported`, `test_the_ceiling_still_applies_when_a_loss_was_stated` | Done |

---

## 6. Education, Prevention and Administration — REQ-20 to REQ-25

Module owner: Masti Choraria

| REQ | Requirement | Design element | Interface | Verified by | Status |
|---|---|---|---|---|---|
| REQ-20 | Display awareness articles | `models/education.py` · `AwarenessContent`; unpublished rows filtered server-side | `GET /api/v1/articles`, `GET /api/v1/articles/{id}`; screen **Awareness** (guest-readable) | `test_education_and_admin.py::test_guest_can_read_articles`, `test_articles_filter_by_category`, `test_unpublished_articles_are_hidden` | Done |
| REQ-21 | Provide scored quizzes | `api/v1/education.py` — scoring server-side; the answer key is never serialised to the client | `GET /api/v1/quizzes`, `GET /api/v1/quizzes/{id}`, `POST /api/v1/quizzes/{id}/attempt` | `test_education_and_admin.py::test_quiz_never_exposes_the_answers`, `test_quiz_scores_and_explains`, `test_unanswered_question_scores_zero_without_erroring` | Done |
| REQ-22 | Admin manages content | Create/publish guarded by the admin role | `POST /api/v1/articles`, `PATCH /api/v1/articles/{id}` | `test_education_and_admin.py::test_only_admin_creates_articles`, `test_admin_can_unpublish_an_article` | Done |
| REQ-23 | Admin manages users and roles | `api/v1/admin.py` — admin-only on the **router**, so a new route cannot ship unprotected; last-admin guard | `GET /api/v1/admin/users`, `PATCH .../role`, `PATCH .../active` | `test_education_and_admin.py::test_admin_can_change_a_role`, `test_admin_can_deactivate_a_user`, `test_last_administrator_cannot_be_deactivated`, `test_second_admin_makes_deactivation_possible`, `test_admin_routes_are_closed_to_everyone_else`, `test_auth.py::test_deactivated_account_loses_access_immediately` | Done |
| REQ-24 | Analytics dashboard | `api/v1/admin.py` · `analytics` — counts by status, category and recovery outcome, computed in SQL | `GET /api/v1/admin/analytics`; screen **Admin** | `test_education_and_admin.py::test_analytics_counts_reports_and_categories`, `test_analytics_on_an_empty_system_does_not_divide_by_zero` | Done |
| REQ-25 | Manage blacklist / whitelist | `models/detection.py` · `BlacklistEntry`; values normalised on write, duplicates refused | `GET/POST/DELETE /api/v1/admin/blacklist` | `test_education_and_admin.py::test_blacklist_entries_are_normalised`, `test_duplicate_blacklist_entry_is_rejected`, `test_blacklist_entry_can_be_removed` | Done — blacklist only; a whitelist is not implemented and is not reached by any code path |

---

## 7. Non-functional and SRS-section traceability

The numbered requirements are not the whole specification. These clauses are
traced the same way.

| SRS clause | Requirement | Where it is met | Verified by |
|---|---|---|---|
| 2.3 | Four user classes, guest unauthenticated | `models/enums.py` · `Role`; `api/deps.py` · `get_optional_user()` | `test_auth.py`, `test_guest_can_read_articles` |
| 2.4 | PostgreSQL in deployment | `render.yaml`, `docker-compose.yml`; SQLite only as a local fallback, and the app says so | `test_regressions.py::test_sqlite_is_reported_as_unsafe_for_production` |
| 2.6 | Third-party unavailability degrades, never breaks | `services/ml_client.py` returns `None`; `services/notifications.py` persists first | `test_ml_integration.py` (5 client-failure tests) |
| 3.2 | Model as an independently deployable service | `ml/` with its own Dockerfile and health check | `ml/test_service.py::test_health_is_always_answerable` |
| 3.3 | Uploads size-limited, scanned, encrypted | `services/storage.py` — 10 MB, content-type allowlist, EICAR-detecting scan, AES-256-GCM | `test_evidence.py::test_upload_is_encrypted_at_rest` + 4 rejection tests |
| 5.1.2 | Score shown with a brief explanation | Linear model; reasons are the actual coefficient contributions | `ml/test_explanations.py` (6 tests) |
| 6.1 | 500 concurrent users, pages < 3 s | `api/pagination.py` — default 100, hard ceiling 500 | `test_regressions.py::test_report_list_is_windowed`, `test_case_list_is_windowed`, `test_an_unreasonable_page_size_is_refused`. **Load figure itself unverified** — see `test-plan.md` §9 |
| 6.2 | The score is advisory, not a determination | Advisory notice returned with every score | `test_detection.py::test_score_is_always_labelled_advisory` |
| 6.3 | RBAC, audit of logins / evidence access / status changes | `api/deps.py`, `services/audit.py`, `services/throttle.py` | `test_auth.py` (12), `test_regressions.py` throttle tests (3) |
| 7 | Legal disclaimer on generated documents | `services/reports_pdf.py` · `DISCLAIMER` on every page | `test_recovery.py` PDF tests |
| Appendix B | Reference format, field sets, rupee formatting | `services/refs.py`, `services/reports_pdf.py` | `test_report_references_are_unique`, PDF tests |
| — | Schema can change after first deployment | Alembic, auto-upgrade at start-up, single head | `test_migrations.py` (4) |
| — | No unsafe production boot | `core/config.py` · `enforce_production_safety()` before any DB access | `test_regressions.py::test_production_refuses_to_start_when_unsafe` + 4 configuration tests |

---

## 8. Backward traceability — every test file to its requirements

| Test file | Tests | Covers |
|---|---|---|
| `backend/tests/test_auth.py` | 12 | REQ-23, SRS 6.3 |
| `backend/tests/test_custody.py` | 8 | REQ-11, REQ-13 |
| `backend/tests/test_detection.py` | 13 | REQ-1 – REQ-4, REQ-6, SRS 6.2 |
| `backend/tests/test_education_and_admin.py` | 19 | REQ-20 – REQ-25, REQ-4 |
| `backend/tests/test_evidence.py` | 16 | REQ-10, REQ-11, REQ-13, SRS 3.3, 6.3 |
| `backend/tests/test_migrations.py` | 4 | schema evolution (no numbered REQ) |
| `backend/tests/test_ml_integration.py` | 15 | REQ-2, REQ-5, REQ-6, REQ-7, SRS 2.6 |
| `backend/tests/test_recovery.py` | 14 | REQ-15 – REQ-19, SRS 7, Appendix B |
| `backend/tests/test_regressions.py` | 18 | REQ-9, REQ-19, SRS 6.1, 6.3, deployment safety |
| `backend/tests/test_reports_and_cases.py` | 15 | REQ-5, REQ-8, REQ-9, REQ-12, REQ-14 |
| `ml/tests/test_explanations.py` | 6 | REQ-6, SRS 5.1.2 |
| `ml/tests/test_model_quality.py` | 16 | REQ-2, REQ-3, REQ-7 |
| `ml/tests/test_service.py` | 15 | REQ-1, REQ-2, REQ-3, SRS 3.2 |
| **Total** | **171** | |

No test file exists that traces to nothing, and no requirement in §3 – §6 has an
empty "Verified by" cell. That is the property this document exists to show.

---

## 9. Open gaps, stated rather than smoothed over

| # | Gap | Consequence | Decision |
|---|---|---|---|
| 1 | REQ-7 has no in-application retrain trigger | An administrator cannot retrain from the UI | Deliberate: training is an offline step behind a quality gate. A button would train on a 512 MB free-tier instance with no review of the result |
| 2 | REQ-25 implements a blacklist, not a whitelist | A known-good value cannot be pinned as safe | Not reached by any code path; recorded rather than quietly counted as done |
| 3 | SRS 6.1's 500-user figure is unverified | Concurrency claim rests on structure, not measurement | The unbounded query — the structural fault — is fixed and tested; load testing is out of scope for this term |
| 4 | Notification dispatch logs instead of sending | Victims see notifications in the system, not in their inbox | Gateway integration point exists; no credentials wired, per SRS 2.6 third-party scope |
| 5 | Malware scan is a hook with a real interface | A real malicious file would not be caught | Honest placeholder: it detects the EICAR test string, and the interface is the one a scanner would plug into |
