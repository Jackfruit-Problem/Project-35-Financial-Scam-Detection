"""Risk scoring. REQ-1 to REQ-6.

Two-stage by design, matching SRS 5.1.2: the blacklist is consulted *before*
the model, because a known-fraudulent UPI ID is a fact and a model score is an
opinion. A blacklist hit short-circuits to 100 and never calls the model.

The scorer behind score_text() is deliberately swappable. Today it is a
transparent rule set (model_version "rules-v0") so the whole pipeline works
end to end with no trained artefact; the ML service replaces it by
implementing the same call and bumping model_version. Nothing else changes.
"""
import re
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.detection import BlacklistEntry, DetectionLog
from app.models.enums import RiskBand

MODEL_VERSION = "rules-v0"

# Signals drawn from common Indian scam patterns: urgency, payment demand,
# credential requests, and lookalike/shortened links.
_SIGNALS: list[tuple[str, int, str]] = [
    (r"\b(urgent|immediately|within \d+ (hours?|minutes?)|last chance)\b", 15, "urgency pressure"),
    (r"\b(kyc|aadhaar|pan card|cvv|otp|pin|password)\b", 20, "credential or KYC request"),
    (r"\b(lottery|prize|jackpot|you have won|reward)\b", 20, "unexpected windfall"),
    (r"\b(guaranteed returns?|double your money|risk[- ]free profit)\b", 25, "investment lure"),
    (r"\b(bit\.ly|tinyurl|t\.me|rb\.gy|is\.gd)\b", 15, "shortened link"),
    (r"\b(instant loan|pre[- ]approved loan|no documents)\b", 15, "loan-app pattern"),
    (r"\b(account (will be )?(blocked|suspended|frozen))\b", 20, "account-threat pressure"),
    (r"@(okaxis|okhdfcbank|oksbi|okicici|ybl|paytm|upi)\b", 10, "UPI handle present"),
]

_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
_UPI_RE = re.compile(r"\b[\w.\-]{2,}@[a-z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"\b(?:\+?91[\-\s]?)?[6-9]\d{9}\b")


def band_for(score: int) -> RiskBand:
    """REQ-3: configurable thresholds, so the bands can be tuned without a redeploy."""
    if score >= settings.RISK_HIGH_THRESHOLD:
        return RiskBand.HIGH
    if score >= settings.RISK_MEDIUM_THRESHOLD:
        return RiskBand.MEDIUM
    return RiskBand.LOW


def extract_indicators(text: str) -> dict[str, list[str]]:
    """Pull the checkable artefacts out of free text for the blacklist lookup."""
    return {
        "url": _URL_RE.findall(text),
        "upi_id": _UPI_RE.findall(text),
        "phone": _PHONE_RE.findall(text),
    }


def check_blacklist(db: Session, text: str) -> BlacklistEntry | None:
    """REQ-4: consulted before the model runs."""
    indicators = extract_indicators(text)
    for entry_type, values in indicators.items():
        for value in values:
            hit = db.scalars(
                select(BlacklistEntry).where(
                    BlacklistEntry.entry_type == entry_type,
                    BlacklistEntry.value == value.lower().rstrip("/"),
                )
            ).first()
            if hit:
                return hit
    return None


def score_text(text: str) -> tuple[int, list[str]]:
    """Advisory score on 0-100 (SRS 6.2), plus the reasons behind it.

    Returning the reasons is not decoration: SRS 5.1.2 requires the score be
    shown "along with a brief explanation", and an unexplained number is not
    something an investigator can act on.
    """
    lowered = text.lower()
    score = 0
    reasons: list[str] = []

    for pattern, weight, label in _SIGNALS:
        if re.search(pattern, lowered):
            score += weight
            reasons.append(label)

    return min(score, 100), reasons


def analyse(
    db: Session, text: str, *, requested_by_id: int | None = None
) -> dict:
    """Full pipeline: blacklist, then model, then log. REQ-6 logs every request."""
    started = time.perf_counter()

    hit = check_blacklist(db, text)
    if hit:
        score, reasons, matched = 100, [f"matches blacklisted {hit.entry_type}"], True
    else:
        score, reasons = score_text(text)
        matched = False

    band = band_for(score)
    latency_ms = int((time.perf_counter() - started) * 1000)

    db.add(
        DetectionLog(
            requested_by_id=requested_by_id,
            input_text=text,
            risk_score=score,
            risk_band=band,
            matched_blacklist=matched,
            model_version=MODEL_VERSION,
            latency_ms=latency_ms,
        )
    )

    return {
        "risk_score": score,
        "risk_band": band,
        "reasons": reasons or ["no known scam indicators detected"],
        "matched_blacklist": matched,
        "model_version": MODEL_VERSION,
        "latency_ms": latency_ms,
        # SRS 6.2 and 6.5: the score never stands alone as a determination.
        "advisory_note": (
            "This score is advisory. A final scam determination requires "
            "review by a human investigator."
        ),
    }
