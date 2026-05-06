from decimal import Decimal

from salik.violations import ANNUAL_FINE_CAP, FINE_SCHEDULE, ViolationRegistry


def test_first_three_offences_follow_schedule():
    reg = ViolationRegistry()
    plate = "DXB-X-1"
    assert reg.record(plate) == FINE_SCHEDULE[0]
    assert reg.record(plate) == FINE_SCHEDULE[1]
    assert reg.record(plate) == FINE_SCHEDULE[2]


def test_fourth_offence_stays_at_top_tier():
    reg = ViolationRegistry()
    plate = "DXB-X-1"
    for _ in range(3):
        reg.record(plate)
    assert reg.record(plate) == FINE_SCHEDULE[-1]


def test_annual_cap_clamps_final_fine():
    reg = ViolationRegistry()
    plate = "DXB-X-1"
    # Pre-load the totals so the next fine would exceed the cap.
    reg._totals[plate] = ANNUAL_FINE_CAP - Decimal("50")
    reg._counts[plate] = 5
    fine = reg.record(plate)
    assert fine == Decimal("50")
    assert reg.total_for(plate) == ANNUAL_FINE_CAP


def test_separate_plates_have_separate_counters():
    reg = ViolationRegistry()
    reg.record("A")
    reg.record("A")
    assert reg.record("B") == FINE_SCHEDULE[0]
    assert reg.count_for("A") == 2
    assert reg.count_for("B") == 1
