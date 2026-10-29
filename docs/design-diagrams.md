# Design Diagrams

Project ID 35 · UE24CS341A · Team Sentinel Squad

SRS section 4 states that a use-case diagram and a supporting
entity-relationship diagram "are maintained as separate design artifacts and
will be included in the project's design documentation". This is that document.

The entity-relationship diagrams below are **generated from the application's
own models**, not drawn by hand, so they cannot drift away from the schema the
system actually creates. Everything else is drawn to match the routes and roles
that exist in the code.

> GitHub renders the diagrams below directly. If you are reading this in a
> plain text editor, paste a block into <https://mermaid.live> to see it.

---

## 1. Use-case diagram

The five actors of SRS 2.3 and what each may do. Guest is unauthenticated.
Every restriction shown here is enforced on the server, not by hiding buttons.

```mermaid
graph LR
    guest([Guest]):::actor
    victim([Victim]):::actor
    investigator([Investigator]):::actor
    officer([Recovery Officer]):::actor
    admin([Administrator]):::actor

    subgraph Detection
        uc1[Analyse a message]
        uc2[Submit scam report]
    end

    subgraph Investigation
        uc3[View assigned cases]
        uc4[Upload evidence]
        uc5[Verify chain of custody]
        uc6[Update case status]
        uc7[Add case notes]
        uc8[Archive evidence]
    end

    subgraph Recovery
        uc9[Raise recovery request]
        uc10[Update recovery status]
        uc11[Download case / recovery PDF]
    end

    subgraph Education
        uc12[Read awareness articles]
        uc13[Take awareness quiz]
    end

    subgraph Administration
        uc14[Manage users and roles]
        uc15[Manage blacklist]
        uc16[Manage awareness content]
        uc17[View analytics and model metrics]
    end

    guest --> uc12
    guest --> uc13

    victim --> uc1
    victim --> uc2
    victim --> uc4
    victim --> uc11
    victim --> uc12
    victim --> uc13

    investigator --> uc1
    investigator --> uc3
    investigator --> uc4
    investigator --> uc5
    investigator --> uc6
    investigator --> uc7
    investigator --> uc8
    investigator --> uc9
    investigator --> uc11

    officer --> uc3
    officer --> uc9
    officer --> uc10
    officer --> uc11

    admin --> uc14
    admin --> uc15
    admin --> uc16
    admin --> uc17

    classDef actor fill:#eaf1fd,stroke:#1f5fbf,stroke-width:1.5px;
```

**Two things the diagram is deliberately strict about.**

A victim appears against *Upload evidence* and *Download PDF* only for their own
case; an investigator only for a case assigned to them. The diagram cannot show
that qualifier, so it is stated here: ownership is checked on every request, and
there are tests that call each endpoint as the wrong role and require a refusal.

*Update recovery status* belongs to the recovery officer and the administrator,
not the investigator. Recording that money moved is a statement about what a
bank did, and it belongs to whoever is liaising with the bank.

---

## 2. Entity-relationship overview

All 15 tables and the relationships between them.
Attributes are omitted here for legibility; the six entities named in SRS
section 4 are shown in full in section 3.

```mermaid
erDiagram
    users ||--o{ audit_logs : "actor"
    users ||--o{ awareness_content : "author"
    users ||--o{ blacklist_entries : "added_by"
    cases ||--|{ case_notes : "case"
    users ||--|{ case_notes : "author"
    scam_reports ||--|{ cases : "report"
    users ||--o{ cases : "assigned_investigator"
    evidence ||--|{ custody_events : "evidence"
    users ||--|{ custody_events : "actor"
    users ||--o{ detection_logs : "requested_by"
    cases ||--|{ evidence : "case"
    users ||--|{ evidence : "uploaded_by"
    users ||--|{ notifications : "user"
    quizzes ||--|{ quiz_attempts : "quiz"
    users ||--o{ quiz_attempts : "user"
    quizzes ||--|{ quiz_questions : "quiz"
    cases ||--|{ recovery_requests : "case"
    users ||--|{ recovery_requests : "raised_by"
    users ||--o{ scam_reports : "reporter"
```

Read `||--|{` as "one to many, required" and `||--o{` as "one to many,
optional". `users` sits at the centre because almost every record names the
person responsible for it, which is what makes the audit trail in SRS 6.3
possible.

---

## 3. Core entities in detail

The six entities SRS section 4 names: User, Report, Case, Evidence,
RecoveryRequest and AwarenessContent.

```mermaid
erDiagram
    users ||--o{ scam_reports : "reporter"
    scam_reports ||--|{ cases : "report"
    users ||--o{ cases : "assigned_investigator"
    cases ||--|{ evidence : "case"
    users ||--|{ evidence : "uploaded_by"
    cases ||--|{ recovery_requests : "case"
    users ||--|{ recovery_requests : "raised_by"
    users ||--o{ awareness_content : "author"
    users {
        int id "PK"
        string_60 full_name
        string_255 email "UK"
        string_15 phone
        string_255 hashed_password
        string_30 role
        bool is_active
        datetime created_at
    }
    scam_reports {
        int id "PK"
        string_12 report_ref "UK"
        int reporter_id "FK"
        string_60 reporter_name
        string_15 reporter_contact
        date report_date
        string_30 category
        text description
        decimal amount_involved
        bool evidence_attached
        int risk_score
        string_10 risk_band
        datetime created_at
    }
    cases {
        int id "PK"
        string_12 case_ref "UK"
        int report_id "FK UK"
        int assigned_investigator_id "FK"
        string_25 status
        datetime updated_at
        datetime created_at
    }
    evidence {
        int id "PK"
        int case_id "FK"
        int uploaded_by_id "FK"
        string_255 filename
        string_512 stored_path
        string_100 content_type
        int size_bytes
        string_64 sha256
        bool is_archived
        text archive_reason
        datetime created_at
    }
    recovery_requests {
        int id "PK"
        int case_id "FK UK"
        int raised_by_id "FK"
        string_120 bank_name
        string_11 ifsc_code
        string_20 account_number
        decimal amount_reported
        decimal amount_recovered
        string_25 status
        text remarks
        datetime updated_at
        datetime created_at
    }
    awareness_content {
        int id "PK"
        string_200 title
        string_30 category
        text body
        bool is_published
        int author_id "FK"
        datetime created_at
    }
```

Notes that matter when reading this:

- `scam_reports.report_ref` and `cases.case_ref` are the 12-character
  human-facing references from SRS Appendix B. The integer `id` columns are
  internal and never shown to a user.
- `evidence.stored_path` is recorded **relative to the evidence root**, not as
  an absolute path. An absolute path would pin the database to one machine and
  one folder, and moving either would orphan every file.
- `evidence.sha256` is the digest of the *plaintext*, so it stays comparable
  with a hash the submitter or a court computes from the original file.
- `recovery_requests.amount_reported` of 0 means "not stated" rather than
  "nothing was lost", because SRS Appendix B makes the amount optional.

---

## 4. Full table reference

| Table | Columns | Purpose |
|---|---|---|
| `audit_logs` | 6 | Security-relevant actions: logins, evidence access, status changes (SRS 6.3). |
| `awareness_content` | 7 | Public awareness articles (REQ-20). |
| `blacklist_entries` | 6 | Known fraudulent URLs, numbers and UPI IDs (REQ-4, REQ-25). |
| `case_notes` | 5 | Attributed, timestamped investigator notes (REQ-14). |
| `cases` | 7 | The investigation record opened for a report (REQ-8). |
| `custody_events` | 8 | The hash-chained chain of custody (REQ-11). |
| `detection_logs` | 9 | Every risk-scoring request and its result (REQ-6). |
| `evidence` | 11 | Uploaded files, encrypted at rest, never deleted (REQ-10, REQ-13). |
| `notifications` | 7 | Status-change notices to victims, stored before dispatch (REQ-18). |
| `quiz_attempts` | 6 | Scored attempts, for the analytics in REQ-24. |
| `quiz_questions` | 6 | Questions and options; the answer key never leaves the server. |
| `quizzes` | 5 | Awareness quizzes (REQ-21). |
| `recovery_requests` | 12 | Fund-recovery tracking against a case (REQ-15 to REQ-19). |
| `scam_reports` | 13 | One submission by a victim. Field lengths follow SRS Appendix B. |
| `users` | 8 | Every account, with the role that governs what it may do. |

---

## 5. The chain of custody

The one part of the data model that is not an ordinary table. REQ-11 requires
evidence handling to be immutable; a normal audit table is one `UPDATE` away
from being rewritten, and nothing about the table would reveal it.

Each custody entry contains a SHA-256 digest computed over its own contents
**together with the previous entry's digest**. Altering or deleting any
historical entry therefore breaks verification at that link and at every link
after it.

```mermaid
graph LR
    G["GENESIS<br/>000…000"] --> E1
    E1["Entry 1 — uploaded<br/>prev: 000…000<br/>hash: 9019…"] --> E2
    E2["Entry 2 — viewed<br/>prev: 9019…<br/>hash: 0135…"] --> E3
    E3["Entry 3 — downloaded<br/>prev: 0135…<br/>hash: 7a4c…"]

    classDef ok fill:#e6f4ec,stroke:#1a7f4b;
    class E1,E2,E3 ok;
```

If entry 2 is edited directly in the database, its recomputed digest no longer
matches the stored one, and entry 3's `prev` no longer matches entry 2 either.
Verification reports the first broken link by id. Two separate facts are
checked: whether the *log* was rewritten, and whether the *file* behind it was
swapped — a file can be replaced without touching the log, and the digest
catches that independently.

---

## 6. How a report moves through the system

The sequence that joins the four modules. Everything after step 4 depends on the
risk band decided in step 3.

```mermaid
sequenceDiagram
    actor V as Victim
    participant W as Web app
    participant A as API
    participant M as Model service
    participant D as Database

    V->>W: Submit scam report
    W->>A: POST /api/v1/reports
    A->>D: Check blacklist (REQ-4)
    alt Identifier is blacklisted
        D-->>A: Match found
        Note over A: Score 100 — a recorded fact,<br/>the model is not consulted
    else Not blacklisted
        A->>M: POST /predict
        alt Model answers
            M-->>A: probability + reasons
        else Service unavailable
            Note over A: Falls back to the built-in rules<br/>so the report can still be filed (SRS 2.6)
        end
    end
    A->>D: Store report with score and band
    A->>D: Open case with generated reference (REQ-8)
    alt Band is High
        A->>D: Assign to least-loaded active investigator (REQ-5, REQ-9)
    else Low or Medium
        Note over A: Stays NEW for human triage
    end
    A->>D: Write detection log (REQ-6) and audit entry (SRS 6.3)
    A-->>W: Report ref, case ref, score, reasons
    W-->>V: Confirmation with the reasons behind the score
```

---

## 7. Deployment view

Three services, as SRS 3.2 requires: the model is separately deployable so it
can be retrained or replaced without touching the application.

```mermaid
graph TB
    subgraph Browser
        UI["React application<br/>port 5173 in development"]
    end

    subgraph Server
        API["FastAPI application<br/>port 8000"]
        ML["Model service<br/>port 8001<br/>TF-IDF → logistic regression"]
    end

    subgraph Storage
        DB[("PostgreSQL<br/>SQLite for local runs")]
        FS[["Encrypted evidence store<br/>AES-256-GCM"]]
    end

    GW["Email / SMS gateway<br/>(stubbed — SRS 2.6)"]

    UI -->|HTTPS, JSON| API
    API -->|HTTP, JSON| ML
    API --> DB
    API --> FS
    API -.->|best effort| GW

    classDef ext fill:#f6f7f9,stroke:#9aa4b2,stroke-dasharray: 4 3;
    class GW ext;
```

The dashed link is deliberate. Notifications are written to the database before
dispatch and dispatch failures are swallowed, because SRS 2.6 requires gateway
unavailability to degrade notifications rather than break the system. The same
reasoning applies to the model service: the API starts and serves whether or not
it is reachable.

---

## Regenerating this document

The diagrams in sections 2, 3 and 4 come from the application's models. After
changing a model, regenerate rather than editing by hand:

```
backend\.venv\Scripts\python.exe docs\gen_diagrams.py
```
