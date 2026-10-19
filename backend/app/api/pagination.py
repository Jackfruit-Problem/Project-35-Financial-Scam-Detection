"""Shared list-window parameters.

SRS 6.1 asks for 500 concurrent users and three-second page loads. An
unbounded list query cannot honour either once the case load is real: it grows
without limit, and a single request can pull the whole table into memory.

A generous default so no existing screen changes behaviour, and a hard ceiling
so no caller can ask for everything.
"""
from dataclasses import dataclass

from fastapi import Query

DEFAULT_LIMIT = 100
MAX_LIMIT = 500


@dataclass
class Page:
    limit: int
    offset: int


def page_params(
    limit: int = Query(
        DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Rows to return, at most 500."
    ),
    offset: int = Query(0, ge=0, description="Rows to skip."),
) -> Page:
    return Page(limit=limit, offset=offset)
