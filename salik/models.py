"""Domain types: Vehicle, Transaction, Account."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from salik.gates import Gate
from salik.tariff import MIN_TOPUP


@dataclass
class Vehicle:
    plate: str           # e.g. "DXB-A-12345"
    nickname: str = ""


@dataclass
class Transaction:
    timestamp: datetime
    gate: Gate | None    # None for top-ups (not gate-bound)
    plate: str           # "-" for top-ups
    amount: Decimal      # negative = debit, positive = credit
    kind: str            # "toll" | "topup" | "fine" | "free_pass"
    balance_after: Decimal
    id: str = field(default_factory=lambda: uuid4().hex[:8])


@dataclass
class Account:
    holder_name: str
    emirates_id: str
    balance: Decimal = Decimal("0.00")
    vehicles: dict[str, Vehicle] = field(default_factory=dict)
    ledger: list[Transaction] = field(default_factory=list)
    fine_count_this_year: int = 0
    fines_this_year: Decimal = Decimal("0.00")

    def link_vehicle(self, vehicle: Vehicle) -> None:
        self.vehicles[vehicle.plate] = vehicle

    def top_up(self, amount: Decimal, *, when: datetime | None = None) -> Transaction:
        if amount < MIN_TOPUP:
            raise ValueError(f"Minimum top-up is AED {MIN_TOPUP}")
        self.balance += amount
        tx = Transaction(
            timestamp=when or datetime.now(),
            gate=None,
            plate="-",
            amount=amount,
            kind="topup",
            balance_after=self.balance,
        )
        self.ledger.append(tx)
        return tx
