"""Generate docs/design-diagrams.md from the live SQLAlchemy metadata.

The entity-relationship section is derived from the models rather than drawn by
hand, so it cannot quietly drift away from the schema the application actually
creates. Re-run this after any model change.
"""
import sys
from pathlib import Path

# Located from this file rather than hard-coded, so it works for anyone who
# clones the repository and wherever the project folder happens to live.
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

import app.models  # noqa: F401,E402  (registers every table)
from app.db.base import Base  # noqa: E402

OUT = REPO / "docs" / "design-diagrams.md"

# The six entities SRS section 4 names explicitly. Shown with their attributes;
# the rest appear in the relationship overview and the reference table.
SRS_CORE = [
    "users", "scam_reports", "cases", "evidence", "recovery_requests",
    "awareness_content",
]

PURPOSE = {
    "users": "Every account, with the role that governs what it may do.",
    "scam_reports": "One submission by a victim. Field lengths follow SRS Appendix B.",
    "cases": "The investigation record opened for a report (REQ-8).",
    "case_notes": "Attributed, timestamped investigator notes (REQ-14).",
    "evidence": "Uploaded files, encrypted at rest, never deleted (REQ-10, REQ-13).",
    "custody_events": "The hash-chained chain of custody (REQ-11).",
    "recovery_requests": "Fund-recovery tracking against a case (REQ-15 to REQ-19).",
    "notifications": "Status-change notices to victims, stored before dispatch (REQ-18).",
    "awareness_content": "Public awareness articles (REQ-20).",
    "quizzes": "Awareness quizzes (REQ-21).",
    "quiz_questions": "Questions and options; the answer key never leaves the server.",
    "quiz_attempts": "Scored attempts, for the analytics in REQ-24.",
    "blacklist_entries": "Known fraudulent URLs, numbers and UPI IDs (REQ-4, REQ-25).",
    "detection_logs": "Every risk-scoring request and its result (REQ-6).",
    "audit_logs": "Security-relevant actions: logins, evidence access, status changes (SRS 6.3).",
}


def mermaid_type(column) -> str:
    """A readable type name for the diagram, not the full SQL type."""
    name = type(column.type).__name__.lower()
    mapping = {
        "integer": "int", "string": "string", "text": "text", "boolean": "bool",
        "datetime": "datetime", "date": "date", "numeric": "decimal", "float": "float",
    }
    base = mapping.get(name, name)
    length = getattr(column.type, "length", None)
    if base == "string" and length:
        return f"string_{length}"
    return base


def relationship_overview(metadata) -> str:
    """All fifteen tables, relationships only. Attributes would make it unreadable."""
    lines = ["erDiagram"]
    seen = set()
    for name in sorted(metadata.tables):
        table = metadata.tables[name]
        for column in table.columns:
            for fk in column.foreign_keys:
                parent = fk.column.table.name
                # One line per (parent, child, column) so two links between the
                # same pair -- cases has two -- both appear.
                label = column.name.removesuffix("_id")
                key = (parent, name, label)
                if key in seen:
                    continue
                seen.add(key)
                optional = "o" if column.nullable else "|"
                lines.append(f'    {parent} ||--{optional}{{ {name} : "{label}"')
    return "\n".join(lines)


def detailed(metadata, tables) -> str:
    lines = ["erDiagram"]

    # Relationships first, so the renderer groups the boxes sensibly.
    emitted = set()
    for name in tables:
        table = metadata.tables[name]
        for column in table.columns:
            for fk in column.foreign_keys:
                parent = fk.column.table.name
                if parent not in tables:
                    continue
                label = column.name.removesuffix("_id")
                key = (parent, name, label)
                if key in emitted:
                    continue
                emitted.add(key)
                optional = "o" if column.nullable else "|"
                lines.append(f'    {parent} ||--{optional}{{ {name} : "{label}"')

    for name in tables:
        table = metadata.tables[name]
        lines.append(f"    {name} {{")
        for column in table.columns:
            marks = []
            if column.primary_key:
                marks.append("PK")
            if column.foreign_keys:
                marks.append("FK")
            if column.unique:
                marks.append("UK")
            suffix = f' "{" ".join(marks)}"' if marks else ""
            lines.append(f"        {mermaid_type(column)} {column.name}{suffix}")
        lines.append("    }")
    return "\n".join(lines)


def reference_table(metadata) -> str:
    rows = ["| Table | Columns | Purpose |", "|---|---|---|"]
    for name in sorted(metadata.tables):
        table = metadata.tables[name]
        purpose = PURPOSE.get(name, "")
        rows.append(f"| `{name}` | {len(table.columns)} | {purpose} |")
    return "\n".join(rows)


metadata = Base.metadata

doc = f"""# Design Diagrams

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

All {len(metadata.tables)} tables and the relationships between them.
Attributes are omitted here for legibility; the six entities named in SRS
section 4 are shown in full in section 3.

```mermaid
{relationship_overview(metadata)}
```

Read `||--|{{` as "one to many, required" and `||--o{{` as "one to many,
optional". `users` sits at the centre because almost every record names the
person responsible for it, which is what makes the audit trail in SRS 6.3
possible.

---

## 3. Core entities in detail

The six entities SRS section 4 names: User, Report, Case, Evidence,
RecoveryRequest and AwarenessContent.

```mermaid
{detailed(metadata, SRS_CORE)}
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

{reference_table(metadata)}

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
backend\\.venv\\Scripts\\python.exe docs\\gen_diagrams.py
```
"""

OUT.write_text(doc, encoding="utf-8")
print(f"written: {OUT}")
print(f"tables documented: {len(metadata.tables)}")
print(f"lines: {len(doc.splitlines())}")
