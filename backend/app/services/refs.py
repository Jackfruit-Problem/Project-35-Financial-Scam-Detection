"""Human-facing identifiers. Appendix B: 12 characters, alphanumeric.

Format: PREFIX + YYMM + 5 random base32 chars, e.g. RPT2609X7K2Q (12 chars).
Random rather than sequential so a case reference does not leak how many
reports the system has received, and so two reports created in the same second
cannot collide.
"""
import secrets

from app.db.base import utcnow

# Crockford-style alphabet: no I, L, O, U -- avoids misreading in printed reports.
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _suffix(length: int = 5) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def new_report_ref() -> str:
    return f"RPT{utcnow():%y%m}{_suffix()}"


def new_case_ref() -> str:
    return f"CSE{utcnow():%y%m}{_suffix()}"
