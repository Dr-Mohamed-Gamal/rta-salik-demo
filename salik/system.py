"""SalikSystem — orchestrates accounts, vehicles, and gantry pass-throughs."""

from datetime import datetime
from decimal import Decimal

from salik.gates import Gate
from salik.models import Account, Transaction, Vehicle
from salik.tariff import LOW_BALANCE_THRESHOLD, toll_for
from salik.violations import ViolationRegistry


class SalikSystem:
    def __init__(self) -> None:
        self._accounts: dict[str, Account] = {}      # by emirates_id
        self._plate_index: dict[str, Account] = {}   # plate -> account
        self.violations = ViolationRegistry()

    # --- registration ----------------------------------------------------

    def register_account(self, holder_name: str, emirates_id: str) -> Account:
        if emirates_id in self._accounts:
            raise ValueError("Account already exists for this Emirates ID")
        acc = Account(holder_name=holder_name, emirates_id=emirates_id)
        self._accounts[emirates_id] = acc
        return acc

    def link_vehicle(self, emirates_id: str, vehicle: Vehicle) -> None:
        acc = self._accounts[emirates_id]
        if vehicle.plate in self._plate_index:
            raise ValueError(f"Plate {vehicle.plate} is already linked")
        acc.link_vehicle(vehicle)
        self._plate_index[vehicle.plate] = acc

    # --- runtime ---------------------------------------------------------

    def pass_through(self, plate: str, gate: Gate, when: datetime) -> Transaction:
        """A vehicle passes a gantry. Returns the resulting transaction."""
        amount = toll_for(when)
        account = self._plate_index.get(plate)

        if amount == 0:
            balance_after = account.balance if account else Decimal("0")
            tx = Transaction(when, gate, plate, Decimal("0"), "free_pass", balance_after)
            if account:
                account.ledger.append(tx)
            return tx

        if account is None:
            fine = self.violations.record(plate)
            return Transaction(when, gate, plate, -fine, "fine", Decimal("0"))

        if account.balance < amount:
            fine = self.violations.record(plate)
            account.fine_count_this_year += 1
            account.fines_this_year += fine
            tx = Transaction(when, gate, plate, -fine, "fine", account.balance)
            account.ledger.append(tx)
            return tx

        account.balance -= amount
        tx = Transaction(when, gate, plate, -amount, "toll", account.balance)
        account.ledger.append(tx)
        return tx

    # --- queries ---------------------------------------------------------

    def account_for_plate(self, plate: str) -> Account | None:
        return self._plate_index.get(plate)

    def low_balance_alerts(self) -> list[Account]:
        return [a for a in self._accounts.values()
                if a.balance < LOW_BALANCE_THRESHOLD]
