from datetime import datetime
from decimal import Decimal

from salik.tariff import OFFPEAK_TOLL, PEAK_TOLL, toll_for


# A known Monday (weekday=0) and a known Sunday (weekday=6).
MON = datetime(2026, 5, 4)
SUN = datetime(2026, 5, 3)


def test_free_window_applies_every_day():
    assert toll_for(MON.replace(hour=2, minute=0)) == 0
    assert toll_for(SUN.replace(hour=5, minute=59)) == 0


def test_sunday_is_free_all_day():
    assert toll_for(SUN.replace(hour=8)) == 0
    assert toll_for(SUN.replace(hour=18)) == 0


def test_weekday_morning_peak():
    assert toll_for(MON.replace(hour=7, minute=30)) == PEAK_TOLL


def test_weekday_evening_peak():
    assert toll_for(MON.replace(hour=17)) == PEAK_TOLL


def test_weekday_offpeak_midday():
    assert toll_for(MON.replace(hour=12)) == OFFPEAK_TOLL


def test_peak_window_is_half_open():
    # 10:00 sharp is no longer peak; 09:59 still is.
    assert toll_for(MON.replace(hour=9, minute=59)) == PEAK_TOLL
    assert toll_for(MON.replace(hour=10, minute=0)) == OFFPEAK_TOLL


def test_returns_decimal():
    assert isinstance(toll_for(MON.replace(hour=12)), Decimal)
