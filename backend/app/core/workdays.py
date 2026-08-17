"""
Working-day calculation utilities.

By default Monday-Friday are working days and Saturday-Sunday are not.
Company holidays can be supplied as a set of `date` objects so they can be
excluded too (e.g. loaded later from a HOLIDAYS table or a config file).
The rest of the codebase should never do naive calendar-day math against
`last_contact_date` etc. -- it should always go through these helpers so
holiday support can be added in one place.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable, Optional, Set


def _to_date(value: date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    return value


def is_working_day(day: date, holidays: Optional[Set[date]] = None) -> bool:
    holidays = holidays or set()
    return day.weekday() < 5 and day not in holidays  # Mon=0 ... Sun=6


def working_days_between(
    start: date | datetime,
    end: date | datetime,
    holidays: Optional[Iterable[date]] = None,
) -> int:
    """
    Number of working days strictly between `start` (exclusive) and `end`
    (inclusive). If end <= start, returns 0.

    Example: a Friday to the following Monday is 1 working day.
    """
    start = _to_date(start)
    end = _to_date(end)
    holiday_set = set(holidays) if holidays else set()

    if end <= start:
        return 0

    count = 0
    current = start + timedelta(days=1)
    while current <= end:
        if is_working_day(current, holiday_set):
            count += 1
        current += timedelta(days=1)
    return count


def add_working_days(
    start: date | datetime,
    days: int,
    holidays: Optional[Iterable[date]] = None,
) -> date:
    """Return the date `days` working days after `start`."""
    start = _to_date(start)
    holiday_set = set(holidays) if holidays else set()

    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if is_working_day(current, holiday_set):
            added += 1
    return current


def working_days_since(
    start: date | datetime,
    holidays: Optional[Iterable[date]] = None,
    reference: Optional[date | datetime] = None,
) -> int:
    """Working days between `start` and now (or a given reference date)."""
    reference = _to_date(reference) if reference else date.today()
    return working_days_between(start, reference, holidays)
