"""Tariff rules: when a pass is free, off-peak (AED 4) or peak (AED 6)."""

from datetime import datetime, time
from decimal import Decimal


PEAK_TOLL = Decimal("6.00")
OFFPEAK_TOLL = Decimal("4.00")
FREE = Decimal("0.00")

# 01:00–06:00 every day is free (RTA "night-time" window).
FREE_WINDOW = (time(1, 0), time(6, 0))

# Weekday peak windows: morning and evening rush.
PEAK_WINDOWS = [
    (time(6, 0), time(10, 0)),
    (time(16, 0), time(20, 0)),
]

LOW_BALANCE_THRESHOLD = Decimal("20.00")
MIN_TOPUP = Decimal("50.00")


def toll_for(when: datetime) -> Decimal:
    """Return the AED toll for a pass at the given timestamp."""
    t = when.time()
    if FREE_WINDOW[0] <= t < FREE_WINDOW[1]:
        return FREE
    # Sunday is a free day. Python: Monday=0 … Sunday=6.
    if when.weekday() == 5:
        return FREE
    if when.weekday() < 5:
        for start, end in PEAK_WINDOWS:
            if start <= t < end:
                return PEAK_TOLL
    return OFFPEAK_TOLL
