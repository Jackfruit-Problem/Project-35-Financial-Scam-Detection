"""Status-change notifications. REQ-18, SRS 2.6.

Every notification is persisted first and dispatched second. That ordering is
deliberate: SRS 2.6 states the email/SMS gateway is a third-party dependency
whose unavailability must degrade notifications without taking down core
functionality. Because the record is written inside the caller's transaction,
a dead gateway leaves a queued notification the victim can still see in-app,
and never rolls back the recovery update that triggered it.
"""
import logging

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.recovery import RecoveryRequest
from app.models.report import Case

logger = logging.getLogger(__name__)


def _dispatch(notification: Notification) -> None:
    """Hand off to the gateway. Logging stands in for SendGrid/Twilio.

    Failures are swallowed on purpose -- see the module docstring. The stored
    row is the source of truth; delivery is best effort.
    """
    try:
        logger.info(
            "notification queued: user=%s channel=%s subject=%s",
            notification.user_id,
            notification.channel,
            notification.subject,
        )
    except Exception:  # pragma: no cover - defensive
        logger.exception("notification dispatch failed")


def notify(
    db: Session,
    *,
    user_id: int | None,
    subject: str,
    body: str,
    channel: str = "email",
) -> Notification | None:
    if user_id is None:
        # An anonymous report has nobody to notify; not an error.
        return None

    notification = Notification(
        user_id=user_id, subject=subject, body=body, channel=channel
    )
    db.add(notification)
    db.flush()
    _dispatch(notification)
    return notification


def notify_recovery_change(
    db: Session,
    *,
    case: Case,
    recovery: RecoveryRequest,
    previous: str | None,
    actor_id: int,
) -> Notification | None:
    """REQ-18: the victim hears about every recovery status change."""
    readable = str(recovery.status).replace("_", " ").title()

    if previous is None:
        subject = f"Recovery assistance started for case {case.case_ref}"
        body = (
            f"A recovery request has been raised for your case {case.case_ref}. "
            f"Current status: {readable}."
        )
    else:
        subject = f"Recovery update for case {case.case_ref}"
        body = (
            f"The recovery status of your case {case.case_ref} changed from "
            f"{str(previous).replace('_', ' ').title()} to {readable}. "
            f"Amount recovered so far: Rs. {float(recovery.amount_recovered or 0):,.2f}."
        )

    return notify(db, user_id=case.report.reporter_id, subject=subject, body=body)
