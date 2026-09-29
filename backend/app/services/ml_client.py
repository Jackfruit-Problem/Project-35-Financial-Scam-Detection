"""Client for the detection model service. SRS 3.2, 2.6.

The model runs as a separate service, so it can be unreachable: not started,
still loading, redeployed, or crashed. None of that may stop a victim filing a
report, so every call here returns None on any failure and the caller falls
back to the built-in rules. A slightly worse score is recoverable; a report
that could not be filed is not.

The timeout is well inside the 5-second budget in REQ-2. On localhost a dead
service refuses the connection immediately, so the fallback costs nothing in
the common case.
"""
import logging
from functools import lru_cache
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _client() -> httpx.Client:
    """One pooled client for the process, not a fresh one per request.

    Measured: calling httpx.post() directly cost roughly 800ms per request
    while the model service itself answered in 17ms. Almost all of it was
    per-call client construction and connection setup. Reusing one client with
    a kept-alive connection removes it. Still well inside REQ-2 either way, but
    a 50x difference is not something to leave on the floor.
    """
    return httpx.Client(
        base_url=settings.ML_SERVICE_URL,
        timeout=settings.ML_TIMEOUT_SECONDS,
    )


def predict(text: str) -> dict[str, Any] | None:
    """Ask the model for a score. None means "use the fallback"."""
    try:
        response = _client().post("/predict", json={"text": text})
        response.raise_for_status()
        body = response.json()
    except httpx.HTTPError as exc:
        # Debug, not warning: with the service deliberately optional, a warning
        # per request would bury real problems in noise.
        logger.debug("model service unavailable, falling back to rules: %s", exc)
        return None
    except ValueError as exc:
        logger.warning("model service returned a non-JSON body: %s", exc)
        return None

    # A reachable but wrong-shaped response is worse than an unreachable one,
    # because it would silently produce nonsense scores. Validate before trust.
    try:
        score = int(body["risk_score"])
        version = str(body["model_version"])
    except (KeyError, TypeError, ValueError):
        logger.warning("model service response missing expected fields: %s", body)
        return None

    if not 0 <= score <= 100:
        logger.warning("model service returned an out-of-range score: %s", score)
        return None

    reasons = body.get("reasons") or []
    if not isinstance(reasons, list):
        reasons = []

    return {
        "risk_score": score,
        "reasons": [str(r) for r in reasons],
        "model_version": version,
        "probability": body.get("probability"),
    }


def info() -> dict[str, Any] | None:
    """The model's measured performance, for the administration dashboard."""
    try:
        response = _client().get("/info")
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.debug("model info unavailable: %s", exc)
        return None
