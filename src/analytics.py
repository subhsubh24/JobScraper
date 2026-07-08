"""Privacy-safe aggregate product analytics — counts ONLY, no PII, no raw per-user events.

This is the PMF-measurement foundation (FACTORY_STANDARD §9): activation (does a new user
reach first value — add a job and see a fit score in session 1?) and engagement are derived
from these daily aggregate counters, NOT from any per-user event log. A row is a single
``(event_type, event_date)`` tally, so the table can never be used to reconstruct an
individual's behaviour and stays tiny (a handful of event types × days).

``record_event()`` is deliberately BEST-EFFORT: analytics must NEVER break, slow, or fail a
user-facing request, so any error is swallowed and the counter simply isn't incremented. It
runs on the request's own session and is only ever called AFTER the endpoint has committed
its real work, so the extra commit persists only the counter row (the same safe pattern the
cross-instance rate limiter uses).
"""
from __future__ import annotations

import logging
from datetime import date as _date, datetime
from typing import Dict, Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.models import AggregateEvent

logger = logging.getLogger("career_operator.analytics")

# The CLOSED set of product events we count. An allowlist keeps the table bounded and stops
# an unbounded ``event_type`` (a future caller typo) from ever creating rows. The first three
# are the activation funnel; the rest measure engagement depth on the paid AI prep features.
EVENT_TYPES = (
    "signup",
    "job_added",
    "fit_score_generated",
    "prep_pack_generated",
    "cover_letter_generated",
    "study_plan_generated",
    "tailored_resume_generated",
    "salary_negotiation_generated",
    "coach_message",
    "learning_plan_generated",
    "profile_enriched",
    "mock_interview_started",
    "mock_interview_answered",
)
_EVENT_TYPE_SET = frozenset(EVENT_TYPES)


def record_event(db: Session, event_type: str, *, when: Optional[_date] = None) -> None:
    """Increment today's aggregate counter for ``event_type``. Best-effort; never raises.

    Unknown event types are ignored (allowlist). On a first-insert race (two instances
    creating the same day's row at once) the IntegrityError is caught and retried as an
    update — mirroring the rate-counter upsert.
    """
    if event_type not in _EVENT_TYPE_SET:
        return
    day = when or datetime.utcnow().date()
    try:
        for _attempt in (1, 2):
            row = (
                db.query(AggregateEvent)
                .filter(
                    AggregateEvent.event_type == event_type,
                    AggregateEvent.event_date == day,
                )
                .first()
            )
            if row is None:
                db.add(AggregateEvent(event_type=event_type, event_date=day, count=1))
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
                    continue  # concurrent insert won the race — retry as an update
                return
            row.count += 1
            db.commit()
            return
    except Exception:  # noqa: BLE001 — analytics is non-critical; never surface to the user
        db.rollback()
        logger.warning(
            "analytics record_event failed for %s; continuing", event_type, exc_info=True
        )


def summary(db: Session) -> Dict[str, object]:
    """All-time aggregate counts by event type (for the owner/growth read endpoint).

    Returns every known event type (0 when unseen) so the shape is stable regardless of what
    has happened yet, plus a derived activation-funnel view. Counts only — no PII.
    """
    rows = (
        db.query(AggregateEvent.event_type, func.sum(AggregateEvent.count))
        .group_by(AggregateEvent.event_type)
        .all()
    )
    seen = {event_type: int(total or 0) for event_type, total in rows}
    totals = {event_type: seen.get(event_type, 0) for event_type in EVENT_TYPES}
    return {
        "totals": totals,
        # Derived activation funnel (aggregate ratios only — the PMF leading indicator).
        "funnel": {
            "signups": totals["signup"],
            "job_added": totals["job_added"],
            "fit_score_generated": totals["fit_score_generated"],
        },
    }
