"""Failed-login throttling. SRS 6.3.

The SRS requires login attempts to be recorded in the audit log, which tells
you afterwards that an account was attacked. It does not require anything that
stops the attack while it is happening, and without that, every weak password
in the system is one short script away.

Deliberate limitations, because the honest version of this is worth more than
a version that pretends to be more:

* Counted per email address, not per IP. An attacker with many addresses can
  spread attempts across accounts, but the common case -- hammering one
  account's password -- is what this blocks.
* Held in memory, so it resets when the process restarts and is not shared
  between workers. With one process that is accurate; with several it becomes
  per-worker and the real limit multiplies. A deployment running more than one
  worker should move this to Redis.
* A successful sign-in clears the counter, so an honest user who mistypes a
  few times and then gets it right is never affected.
"""
import time
from dataclasses import dataclass, field

from app.core.config import settings


@dataclass
class _Attempts:
    count: int = 0
    first_at: float = field(default_factory=time.monotonic)


_failures: dict[str, _Attempts] = {}


def _window_seconds() -> int:
    return settings.LOGIN_LOCKOUT_SECONDS


def seconds_until_retry(key: str) -> int:
    """How long this address must wait, or 0 if it may try now."""
    record = _failures.get(key)
    if record is None or record.count < settings.LOGIN_MAX_FAILURES:
        return 0

    elapsed = time.monotonic() - record.first_at
    remaining = _window_seconds() - elapsed
    if remaining <= 0:
        # The window has passed; the slate is clean.
        _failures.pop(key, None)
        return 0
    return int(remaining) + 1


def record_failure(key: str) -> None:
    record = _failures.get(key)
    now = time.monotonic()

    # A fresh window rather than a rolling one: simpler to reason about, and
    # the difference only matters to an attacker pacing themselves exactly at
    # the limit, who is rate-limited either way.
    if record is None or (now - record.first_at) > _window_seconds():
        _failures[key] = _Attempts(count=1, first_at=now)
        return

    record.count += 1


def record_success(key: str) -> None:
    _failures.pop(key, None)


def reset() -> None:
    """For tests, so one test's failures cannot lock out another's."""
    _failures.clear()
