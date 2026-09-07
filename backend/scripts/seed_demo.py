"""Populate a demo database so the running system has something to show.

Safe to re-run: it wipes and rebuilds the local development database. Never
point this at anything but a local dev database.

    .venv\\Scripts\\python.exe scripts/seed_demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.models.detection import BlacklistEntry  # noqa: E402
from app.models.education import AwarenessContent, Quiz, QuizQuestion  # noqa: E402
from app.models.enums import (  # noqa: E402
    CaseStatus,
    CustodyAction,
    RecoveryStatus,
    Role,
)
from app.models.evidence import Evidence  # noqa: E402
from app.models.recovery import RecoveryRequest  # noqa: E402
from app.models.report import Case, CaseNote, ScamReport  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import custody, detection, refs, storage  # noqa: E402

PASSWORD = "password123"

DEMO_USERS = [
    ("Asha Rao", "victim@fsdiras.example.com", Role.VICTIM),
    ("Ravi Kumar", "victim2@fsdiras.example.com", Role.VICTIM),
    ("Meha Mahajan", "investigator@fsdiras.example.com", Role.INVESTIGATOR),
    ("Zaid Mallik", "investigator2@fsdiras.example.com", Role.INVESTIGATOR),
    ("Masti Choraria", "officer@fsdiras.example.com", Role.RECOVERY_OFFICER),
    ("Mohammed Muaz Iqubal", "admin@fsdiras.example.com", Role.ADMIN),
]

SCAMS = [
    (
        "upi_fraud",
        25000,
        "URGENT: your account will be blocked immediately. Complete KYC now and "
        "share your OTP and PAN card to avoid suspension. Verify at "
        "http://bit.ly/kyc-verify-now",
    ),
    (
        "investment",
        150000,
        "Join our premium trading group for guaranteed returns. Double your money "
        "in 30 days, risk-free profit, last chance to join today.",
    ),
    (
        "loan_app",
        8000,
        "Pre-approved instant loan, no documents needed. Pay a processing fee to "
        "fraudster@ybl and receive funds within minutes.",
    ),
    (
        "phishing",
        0,
        "I got an email that looked like it came from my bank asking me to log in, "
        "but I noticed the address was slightly misspelled and did not click it.",
    ),
    (
        "other",
        3200,
        "Someone called claiming to be from customer support about a refund for a "
        "cancelled order and asked me to install a screen sharing app.",
    ),
]

ARTICLES = [
    (
        "How UPI refund scams work",
        "upi_fraud",
        "A genuine refund never requires you to enter your UPI PIN. Entering your "
        "PIN authorises money leaving your account, never money arriving. If "
        "someone asks you to 'approve' a request to receive a refund, it is a scam.",
    ),
    (
        "Spotting a fake loan app",
        "loan_app",
        "Legitimate lenders are RBI-registered and never ask for an upfront "
        "processing fee paid to a personal UPI ID. Check the lender against the "
        "RBI register before sharing any document.",
    ),
    (
        "Why no bank will ever ask for your OTP",
        "phishing",
        "An OTP exists to prove that you, and only you, approved a transaction. "
        "Bank staff can complete every legitimate task without it. Anyone asking "
        "for an OTP is asking you to approve their transaction, not yours.",
    ),
]

QUIZ = (
    "Can you spot a scam?",
    "phishing",
    [
        (
            "A caller says they are from your bank and needs your OTP to reverse a "
            "fraudulent charge. What should you do?",
            ["Read out the OTP so the charge is reversed",
             "Hang up and call the number on your bank card",
             "Send the OTP by SMS instead, which is safer"],
            1,
            "No bank employee ever needs your OTP. Always call back on a number "
            "you looked up yourself, not one you were given.",
        ),
        (
            "You are promised guaranteed returns of 20% per month. This is:",
            ["A good opportunity if the group has many members",
             "Normal for cryptocurrency investments",
             "Almost certainly a fraud, because no return is guaranteed"],
            2,
            "Guaranteed high returns are the single most reliable marker of "
            "investment fraud. Real markets cannot promise this.",
        ),
        (
            "A loan app asks for a processing fee sent to a personal UPI ID. This is:",
            ["Standard practice for instant loans",
             "A scam, since registered lenders deduct fees from the disbursed amount",
             "Acceptable if the app has good reviews"],
            1,
            "Registered lenders never collect fees to a personal UPI ID before "
            "disbursing a loan.",
        ),
    ],
)

BLACKLIST = [
    ("upi_id", "fraudster@ybl", "Reported in 12 separate cases"),
    ("url", "http://bit.ly/kyc-verify-now", "Phishing page harvesting OTPs"),
    ("phone", "9812345678", "Fake customer-support caller"),
]


def main() -> None:
    print("Rebuilding demo database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    for name, email, role in DEMO_USERS:
        db.add(
            User(
                full_name=name,
                email=email,
                phone="9876543210",
                hashed_password=hash_password(PASSWORD),
                role=role,
            )
        )
    db.flush()

    def by_email(local_part: str) -> User:
        return db.query(User).filter_by(email=f"{local_part}@fsdiras.example.com").one()

    victim = by_email("victim")
    victim2 = by_email("victim2")
    investigator = by_email("investigator")
    admin = by_email("admin")

    for entry_type, value, note in BLACKLIST:
        db.add(
            BlacklistEntry(
                entry_type=entry_type, value=value, note=note, added_by_id=admin.id
            )
        )
    db.flush()

    cases: list[Case] = []
    for index, (category, amount, description) in enumerate(SCAMS):
        reporter = victim if index % 2 == 0 else victim2
        result = detection.analyse(db, description, requested_by_id=reporter.id)

        report = ScamReport(
            report_ref=refs.new_report_ref(),
            reporter_id=reporter.id,
            reporter_name=reporter.full_name,
            reporter_contact="9876543210",
            category=category,
            description=description,
            amount_involved=amount or None,
            risk_score=result["risk_score"],
            risk_band=result["risk_band"],
        )
        db.add(report)
        db.flush()

        case = Case(case_ref=refs.new_case_ref(), report_id=report.id)
        if result["risk_band"] == "high":
            case.assigned_investigator_id = investigator.id
            case.status = CaseStatus.UNDER_INVESTIGATION
        db.add(case)
        db.flush()
        cases.append(case)

        print(
            f"  {case.case_ref}  {category:<11} risk={result['risk_score']:>3} "
            f"({result['risk_band']}) -> {case.status}"
        )

    # Give the first case a full evidence trail so the custody chain is visible.
    lead = cases[0]
    for filename, content, content_type in [
        ("whatsapp-screenshot.png", b"PNG-bytes-standing-in-for-a-screenshot", "image/png"),
        ("bank-statement.pdf", b"%PDF-1.4 statement showing the debit", "application/pdf"),
        ("chatlog-export.txt", b"14:02 unknown: share the OTP\n14:03 me: 449281", "text/plain"),
    ]:
        stored_path, digest = storage.store(
            content, case_ref=lead.case_ref, filename=filename
        )
        evidence = Evidence(
            case_id=lead.id,
            uploaded_by_id=victim.id,
            filename=filename,
            stored_path=stored_path,
            content_type=content_type,
            size_bytes=len(content),
            sha256=digest,
        )
        db.add(evidence)
        db.flush()
        custody.append_event(
            db,
            evidence_id=evidence.id,
            actor_id=victim.id,
            action=CustodyAction.UPLOADED,
            detail=f"sha256={digest}",
        )
        custody.append_event(
            db,
            evidence_id=evidence.id,
            actor_id=investigator.id,
            action=CustodyAction.VIEWED,
        )
    lead.report.evidence_attached = True

    db.add(
        CaseNote(
            case_id=lead.id,
            author_id=investigator.id,
            body="Beneficiary UPI ID traced to a mule account. Bank fraud desk notified.",
        )
    )

    recovery = RecoveryRequest(
        case_id=lead.id,
        raised_by_id=investigator.id,
        bank_name="State Bank of India",
        ifsc_code="SBIN0001234",
        account_number="30123456789",
        amount_reported=lead.report.amount_involved or 0,
        amount_recovered=11000,
        status=RecoveryStatus.PARTIALLY_RECOVERED,
        remarks="Rs. 11,000 held at the beneficiary bank and reversed. Remainder withdrawn.",
    )
    db.add(recovery)

    for title, category, body in ARTICLES:
        db.add(
            AwarenessContent(
                title=title, category=category, body=body, author_id=admin.id
            )
        )

    quiz_title, quiz_category, questions = QUIZ
    quiz = Quiz(title=quiz_title, category=quiz_category)
    db.add(quiz)
    db.flush()
    for prompt, options, correct, explanation in questions:
        db.add(
            QuizQuestion(
                quiz_id=quiz.id,
                prompt=prompt,
                options="\n".join(options),
                correct_index=correct,
                explanation=explanation,
            )
        )

    db.commit()
    # Read what the summary needs before closing: after close() the ORM
    # objects are detached and any unloaded attribute raises.
    lead_ref = lead.case_ref
    case_count = len(cases)
    db.close()

    print(f"\nSeeded {case_count} cases, 3 evidence items, 1 recovery request, "
          f"{len(ARTICLES)} articles, 1 quiz, {len(BLACKLIST)} blacklist entries.")
    print(f"\nAll demo accounts use the password: {PASSWORD}")
    for name, email, role in DEMO_USERS:
        print(f"  {str(role):<17} {email:<34} {name}")
    print(f"\nLead case with full evidence trail: {lead_ref}")


if __name__ == "__main__":
    main()
