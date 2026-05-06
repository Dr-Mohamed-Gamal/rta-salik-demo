"""Salik — RTA Dubai electronic toll system (emulator)."""

from salik.gates import Gate
from salik.models import Account, Transaction, Vehicle
from salik.system import SalikSystem
from salik.tariff import toll_for
from salik.violations import ViolationRegistry

__all__ = [
    "Account",
    "Gate",
    "SalikSystem",
    "Transaction",
    "Vehicle",
    "ViolationRegistry",
    "toll_for",
]
