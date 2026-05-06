from datetime import datetime
from decimal import Decimal

import pytest

from salik import Gate, SalikSystem, Vehicle


MON_PEAK = datetime(2026, 5, 4, 8, 0)        # weekday peak
MON_OFFPEAK = datetime(2026, 5, 4, 12, 0)    # weekday off-peak
MON_FREE = datetime(2026, 5, 4, 3, 0)        # free window


@pytest.fixture
def system_with_account():
    sys = SalikSystem()
    acc = sys.register_account("Fatima", "784-1990-0000001-1")
    sys.link_vehicle(acc.emirates_id, Vehicle("DXB-A-1"))
    acc.top_up(Decimal("100.00"), when=MON_PEAK)
    return sys, acc


def test_peak_pass_debits_six_aed(system_with_account):
    sys, acc = system_with_account
    tx = sys.pass_through("DXB-A-1", Gate.AL_GARHOUD, MON_PEAK)
    assert tx.kind == "toll"
    assert tx.amount == Decimal("-6.00")
    assert acc.balance == Decimal("94.00")


def test_offpeak_pass_debits_four_aed(system_with_account):
    sys, acc = system_with_account
    tx = sys.pass_through("DXB-A-1", Gate.JEBEL_ALI, MON_OFFPEAK)
    assert tx.amount == Decimal("-4.00")
    assert acc.balance == Decimal("96.00")


def test_free_window_does_not_debit(system_with_account):
    sys, acc = system_with_account
    before = acc.balance
    tx = sys.pass_through("DXB-A-1", Gate.AL_BARSHA, MON_FREE)
    assert tx.kind == "free_pass"
    assert tx.amount == 0
    assert acc.balance == before


def test_unregistered_plate_gets_fined():
    sys = SalikSystem()
    tx = sys.pass_through("UNKNOWN-1", Gate.AL_MAKTOUM, MON_PEAK)
    assert tx.kind == "fine"
    assert tx.amount == Decimal("-100")


def test_insufficient_balance_fines_instead_of_tolling(system_with_account):
    sys, acc = system_with_account
    acc.balance = Decimal("1.00")
    tx = sys.pass_through("DXB-A-1", Gate.BUSINESS_BAY, MON_PEAK)
    assert tx.kind == "fine"
    assert acc.balance == Decimal("1.00")  # unchanged — fine is separate
    assert acc.fine_count_this_year == 1


def test_cannot_link_same_plate_twice():
    sys = SalikSystem()
    sys.register_account("A", "id-A")
    sys.register_account("B", "id-B")
    sys.link_vehicle("id-A", Vehicle("DXB-A-1"))
    with pytest.raises(ValueError):
        sys.link_vehicle("id-B", Vehicle("DXB-A-1"))


def test_low_balance_alert(system_with_account):
    sys, acc = system_with_account
    acc.balance = Decimal("5.00")
    alerts = sys.low_balance_alerts()
    assert acc in alerts


def test_minimum_topup_enforced(system_with_account):
    _, acc = system_with_account
    with pytest.raises(ValueError):
        acc.top_up(Decimal("10"))
