"""Generated test cases for violations module - missing HIGH/MEDIUM scenarios.

Covers edge cases not in tests/test_violations.py.
Based on test plan docs/test_plan.md section 2.2.
"""

from decimal import Decimal

import pytest

from salik.violations import ANNUAL_FINE_CAP, ViolationRegistry


def test_annual_cap_at_exact_boundary():
    """Covers V-H6: Annual cap at exactly AED 10,000.00."""
    reg = ViolationRegistry()
    plate = "TEST-1"
    reg._totals[plate] = ANNUAL_FINE_CAP
    reg._counts[plate] = 10
    fine = reg.record(plate)
    assert fine == Decimal("0")


def test_annual_cap_one_cent_below():
    """Covers V-H5: Annual cap at AED 9,999.99 (one cent below)."""
    reg = ViolationRegistry()
    plate = "TEST-1"
    reg._totals[plate] = ANNUAL_FINE_CAP - Decimal("0.01")
    reg._counts[plate] = 10
    fine = reg.record(plate)
    assert fine == Decimal("0.01")


def test_tenth_violation_still_top_tier():
    """Covers V-M1: 10th violation stays at top tier (400)."""
    reg = ViolationRegistry()
    plate = "TEST-1"
    for _ in range(9):
        reg.record(plate)
    fine = reg.record(plate)
    assert fine == Decimal("400")


def test_plate_with_zero_violations():
    """Covers V-M4: Plate with no violations returns zero."""
    reg = ViolationRegistry()
    assert reg.count_for("NEVER-VIOLATED") == 0
    assert reg.total_for("NEVER-VIOLATED") == Decimal("0")


@pytest.mark.parametrize("initial_total,expected_fine,scenario", [
    (Decimal("9900"), Decimal("100"), "V-H7: Room for full 100 fine"),
    (Decimal("9950"), Decimal("50"), "V-H7: Partial fine (50 remaining)"),
    (Decimal("9999"), Decimal("1"), "V-H7: Only 1 AED remaining"),
    (Decimal("10000"), Decimal("0"), "V-H6: At cap exactly"),
])
def test_annual_cap_edge_cases(initial_total, expected_fine, scenario):
    """Covers V-H5, V-H6, V-H7: Various annual cap boundary scenarios."""
    reg = ViolationRegistry()
    plate = "TEST-1"
    reg._totals[plate] = initial_total
    reg._counts[plate] = 1
    fine = reg.record(plate)
    assert fine == expected_fine


def test_registry_state_persistence():
    """Covers V-H11: Registry maintains state across operations."""
    reg = ViolationRegistry()
    plate = "TEST-1"
    reg.record(plate)
    assert reg.count_for(plate) == 1
    assert reg.total_for(plate) == Decimal("100")
    reg.record(plate)
    assert reg.count_for(plate) == 2
    assert reg.total_for(plate) == Decimal("300")
    reg.record(plate)
    assert reg.count_for(plate) == 3
    assert reg.total_for(plate) == Decimal("700")

# Made with Bob
