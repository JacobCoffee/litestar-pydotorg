"""Recurrence rule utilities for events using dateutil.rrule."""

from __future__ import annotations

import datetime
import re
from enum import IntEnum
from typing import TYPE_CHECKING

from dateutil.rrule import DAILY, MONTHLY, WEEKLY, YEARLY, rrule

if TYPE_CHECKING:
    from collections.abc import Iterator


class Frequency(IntEnum):
    """Recurrence frequency constants matching dateutil.rrule."""

    YEARLY = YEARLY
    MONTHLY = MONTHLY
    WEEKLY = WEEKLY
    DAILY = DAILY


FREQUENCY_LABELS = {
    Frequency.YEARLY: "year(s)",
    Frequency.MONTHLY: "month(s)",
    Frequency.WEEKLY: "week(s)",
    Frequency.DAILY: "day(s)",
}

FREQUENCY_TIMEDELTAS = {
    Frequency.YEARLY: datetime.timedelta(days=365),
    Frequency.MONTHLY: datetime.timedelta(days=30),
    Frequency.WEEKLY: datetime.timedelta(days=7),
    Frequency.DAILY: datetime.timedelta(days=1),
}


def create_rrule(
    frequency: Frequency | int,
    interval: int = 1,
    dtstart: datetime.datetime | None = None,
    until: datetime.datetime | None = None,
    count: int | None = None,
) -> rrule:
    """Create a dateutil rrule object.

    Args:
        frequency: Recurrence frequency (YEARLY, MONTHLY, WEEKLY, DAILY)
        interval: Number of frequency units between occurrences
        dtstart: Start date for recurrence
        until: End date for recurrence (exclusive with count)
        count: Maximum number of occurrences (exclusive with until)

    Returns:
        Configured rrule object
    """
    return rrule(
        freq=int(frequency),
        interval=interval,
        dtstart=dtstart,
        until=until,
        count=count,
    )


def get_occurrences(
    rule: rrule,
    after: datetime.datetime | None = None,
    before: datetime.datetime | None = None,
    *,
    inc: bool = False,
) -> Iterator[datetime.datetime]:
    """Get occurrences from a recurrence rule within a date range.

    Args:
        rule: The rrule to generate occurrences from
        after: Only include occurrences after this datetime
        before: Only include occurrences before this datetime
        inc: Include the after/before boundaries

    Yields:
        Occurrence datetimes
    """
    if after and before:
        yield from rule.between(after, before, inc=inc)
    elif after:
        occurrence = rule.after(after, inc=inc)
        if occurrence:
            yield occurrence
    elif before:
        occurrence = rule.before(before, inc=inc)
        if occurrence:
            yield occurrence
    else:
        yield from rule


def next_occurrence(
    rule: rrule,
    after: datetime.datetime | None = None,
) -> datetime.datetime | None:
    """Get the next occurrence from a recurrence rule.

    Args:
        rule: The rrule to get next occurrence from
        after: Find occurrence after this datetime (default: now)

    Returns:
        Next occurrence datetime or None if no more occurrences
    """
    if after is None:
        after = datetime.datetime.now(tz=datetime.UTC)
    return rule.after(after)


def timedelta_parse(string: str) -> datetime.timedelta:
    """Parse a string into a timedelta object.

    Supports formats:
    - "HH:MM:SS" or "D days, HH:MM:SS" (PostgreSQL/SQLite format)
    - "1w 2d 3h 4m 5s" (flexible format with units)
    - "15 min", "2 hours", "1 day" (human readable)

    Args:
        string: Duration string to parse

    Returns:
        Parsed timedelta

    Raises:
        TypeError: If string is not a valid time interval
    """
    string = string.strip()
    if not string:
        msg = f"{string!r} is not a valid time interval"
        raise TypeError(msg)

    # PostgreSQL/SQLite format: "D days, HH:MM:SS" or "HH:MM:SS"
    d = re.match(
        r"^((?P<days>[-+]?\d+) days?,? )?(?P<sign>[-+]?)(?P<hours>\d+):"
        r"(?P<minutes>\d+)(:(?P<seconds>\d+(\.\d+)?))?$",
        string,
    )
    if d:
        d = d.groupdict("0")
        if d["sign"] == "-":
            for k in ("hours", "minutes", "seconds"):
                d[k] = "-" + d[k]
        d.pop("sign", None)
    else:
        # Flexible format: "1w 2d 3h 4m 5s"
        d = re.match(
            r"^((?P<weeks>-?((\d*\.\d+)|\d+))\W*w((ee)?(k(s)?)?)(,)?\W*)?"
            r"((?P<days>-?((\d*\.\d+)|\d+))\W*d(ay(s)?)?(,)?\W*)?"
            r"((?P<hours>-?((\d*\.\d+)|\d+))\W*h(ou)?(r(s)?)?(,)?\W*)?"
            r"((?P<minutes>-?((\d*\.\d+)|\d+))\W*m(in(ute)?(s)?)?(,)?\W*)?"
            r"((?P<seconds>-?((\d*\.\d+)|\d+))\W*s(ec(ond)?(s)?)?)?\W*$",
            string,
        )
        if not d:
            msg = f"{string!r} is not a valid time interval"
            raise TypeError(msg)
        d = d.groupdict("0")

    return datetime.timedelta(**{k: float(v) for k, v in d.items()})


def timedelta_format(
    td: datetime.timedelta,
    display: str = "long",
    sep: str = ", ",
) -> str:
    """Format a timedelta object as a human-readable string.

    Args:
        td: Timedelta to format
        display: Format style - 'minimal', 'short', or 'long'
        sep: Separator between units

    Returns:
        Formatted string representation
    """
    if not isinstance(td, datetime.timedelta):
        msg = "First argument must be a timedelta."
        raise TypeError(msg)

    result = []
    weeks = int(td.days / 7)
    days = td.days % 7
    hours = int(td.seconds / 3600)
    minutes = int((td.seconds % 3600) / 60)
    seconds = td.seconds % 60

    if display == "minimal":
        words = ["w", "d", "h", "m", "s"]
    elif display == "short":
        words = [" wks", " days", " hrs", " min", " sec"]
    else:  # long
        words = [" weeks", " days", " hours", " minutes", " seconds"]

    values = [weeks, days, hours, minutes, seconds]
    for i, value in enumerate(values):
        if value:
            if value == 1 and len(words[i]) > 1:
                result.append(f"{value}{words[i].rstrip('s')}")
            else:
                result.append(f"{value}{words[i]}")

    # Values with less than one second are considered zeros
    if not result:
        result.append(f"0{words[-1]}")

    return sep.join(result)


def frequency_interval_as_timedelta(frequency: Frequency | int, interval: int = 1) -> datetime.timedelta:
    """Convert a frequency and interval to an approximate timedelta.

    Args:
        frequency: Recurrence frequency
        interval: Number of frequency units

    Returns:
        Approximate timedelta for the interval
    """
    freq = Frequency(frequency)
    return interval * FREQUENCY_TIMEDELTAS[freq]
