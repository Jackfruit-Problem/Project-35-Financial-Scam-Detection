# Financial Scam Detection, Investigation, and Recovery Assistance System

**Project ID:** 35
**Course:** UE24CS341A – Software Engineering
**Team:** Sentinel Squad

## Overview

Financial scams — phishing messages, fraudulent UPI payment requests, fake loan
applications, and investment fraud — have grown substantially, causing significant
monetary loss and overwhelming law enforcement and bank fraud desks with
unstructured complaints.

This project is a web-based platform that:

- **Detects** suspicious messages, URLs, and transaction patterns using an AI/ML
  risk-scoring engine.
- **Investigates** reported scams through a structured case-management workflow
  with a verifiable evidence chain of custody.
- **Assists recovery** by tracking fund-recovery status with banks/payment
  gateways and generating standardized reports for banks, police, or the RBI
  Ombudsman.
- **Educates** the public through awareness content and short quizzes to reduce
  future incidents.

## Team

| Team Member | SRN | Responsibility |
|---|---|---|
| Mohammed Muaz Iqubal | PES2UG24AM091 | Recovery & Reporting Assistance |
| Meha Mahajan | PES2UG24AM090 | Investigation & Evidence Management |
| Zaid Mallik | PES2UG24AM093 | Scam Detection & AI/ML |
| Masti Choraria | PES2UG24AM087 | Education, Prevention & Administration |

## Repository Structure

```
.
├── docs/           # Project documentation (SRS, project plan, test plan, design docs)
├── src/            # Application source code
├── tests/          # Test cases and test artifacts
└── README.md
```

## Documentation

| Document | Status | Location |
|---|---|---|
| Software Requirements Specification (v1.0) | ✅ Complete | [`docs/SRS_ProjectID35_FSDIRAS.docx`](docs/SRS_ProjectID35_FSDIRAS.docx) |
| Project Plan | 🔲 Pending | `docs/` |
| Test Plan | 🔲 Pending | `docs/` |
| Design Diagrams | 🔲 Pending | `docs/` |

## System Modules

1. **Scam Detection Engine (AI/ML)** — analyzes text, URLs, and transaction
   metadata to produce a risk score, cross-checked against a maintained
   blacklist.
2. **Investigation & Evidence Management** — case lifecycle management with an
   immutable, timestamped chain of custody for evidence.
3. **Recovery & Reporting Assistance** — recovery-status tracking and
   auto-generated PDF case/recovery reports.
4. **Education, Prevention & Administration** — awareness articles, quizzes,
   and admin controls for users, content, and blacklists.

Full functional and non-functional requirements are detailed in the
[SRS](docs/SRS_ProjectID35_FSDIRAS.docx).

## Getting Started

_Setup instructions will be added here once implementation begins._

## License

This project is developed for academic purposes as part of UE24CS341A –
Software Engineering.
