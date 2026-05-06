"""Generated test cases for tariff module - missing HIGH/MEDIUM scenarios.

Covers boundary conditions not in tests/test_tariff.py.
Based on test plan docs/test_plan.md section 2.1.
"""

from datetime import datetime

import pytest

from salik.tariff import FREE, OFFPEAK_TOLL, PEAK_TOLL, toll_for


MON = datetime(2026, 5, 4)  # Monday
SAT = datetime(2026, 5, 9)  # Saturday
SUN = datetime(2026, 5, 3)  # Sunday


@pytest.mark.parametrize("hour,minute,expected,scenario", [
    (1, 0, FREE, "T-H1: Free window start at 01:00"),
    (5, 59, FREE, "T-H2: Free window end at 05:59"),
    (6, 0, PEAK_TOLL, "T-H3: Transition from free to peak at 06:00"),
    (9, 59, PEAK_TOLL, "T-H5: Morning peak end at 09:59"),
    (10, 0, OFFPEAK_TOLL, "T-H6: Peak to off-peak at 10:00"),
    (16, 0, PEAK_TOLL, "T-H7: Evening peak start at 16:00"),
    (19, 59, PEAK_TOLL, "T-H8: Evening peak end at 19:59"),
    (20, 0, OFFPEAK_TOLL, "T-H9: Peak to off-peak at 20:00"),
    (23, 59, OFFPEAK_TOLL, "T-H12: Before midnight"),
    (0, 0, OFFPEAK_TOLL, "T-H12: After midnight"),
])
def test_time_boundaries_weekday(hour, minute, expected, scenario):
    """Covers time window boundaries on weekdays."""
    dt = MON.replace(hour=hour, minute=minute)
    assert toll_for(dt) == expected


# T-H13 (Leap second handling) is not testable: Python datetime does not support
# leap seconds, and the tariff logic operates at minute granularity.


def test_saturday_is_offpeak_all_day():
    """Covers T-H10: Saturday (weekday=5) is off-peak all day."""
    assert toll_for(SAT.replace(hour=8)) == OFFPEAK_TOLL
    assert toll_for(SAT.replace(hour=17)) == OFFPEAK_TOLL


def test_sunday_free_during_peak_hours():
    """Covers T-H11: Sunday free even during what would be peak hours."""
    assert toll_for(SUN.replace(hour=7)) == FREE
    assert toll_for(SUN.replace(hour=17)) == FREE


def test_free_window_applies_on_saturday():
    """Covers T-M1: Free window applies even on Saturday."""
    assert toll_for(SAT.replace(hour=3)) == FREE


def test_free_window_applies_on_sunday():
    """Covers T-M1: Free window applies even on Sunday."""
    assert toll_for(SUN.replace(hour=3)) == FREE


@pytest.mark.parametrize("weekday_offset,hour,expected", [
    (0, 7, PEAK_TOLL),    # T-M4: Monday morning peak
    (1, 7, PEAK_TOLL),    # Tuesday morning peak
    (2, 7, PEAK_TOLL),    # Wednesday morning peak
    (3, 7, PEAK_TOLL),    # Thursday morning peak
    (4, 7, PEAK_TOLL),    # T-M3: Friday morning peak
    (5, 7, OFFPEAK_TOLL), # T-H10: Saturday morning off-peak
    (6, 7, FREE),         # T-H11: Sunday morning free
])
def test_weekday_rules(weekday_offset, hour, expected):
    """Covers T-M3, T-M4: Verify all weekdays follow correct rules."""
    from datetime import timedelta
    dt = MON.replace(hour=hour) + timedelta(days=weekday_offset)
    assert toll_for(dt) == expected


def test_late_evening_offpeak():
    """Covers T-M2: Off-peak late evening (20:00-00:59)."""
    assert toll_for(MON.replace(hour=22)) == OFFPEAK_TOLL
    assert toll_for(MON.replace(hour=0, minute=30)) == OFFPEAK_TOLL

# Made with Bob
