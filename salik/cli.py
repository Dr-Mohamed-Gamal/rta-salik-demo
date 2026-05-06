"""Demo entry point: simulates a day on Sheikh Zayed Road."""

from datetime import datetime
from decimal import Decimal

from salik.gates import Gate
from salik.models import Transaction, Vehicle
from salik.system import SalikSystem


def _print_tx(tx: Transaction) -> None:
    sign = "+" if tx.amount >= 0 else ""
    gate_name = tx.gate.value if tx.gate else "-"
    print(f"  [{tx.timestamp:%a %H:%M}] {gate_name:<25} "
          f"{tx.plate:<12} {tx.kind:<9} {sign}{tx.amount:>7} AED  "
          f"(bal {tx.balance_after} AED)")


def main() -> None:
    salik = SalikSystem()

    # 1. Open account, link two vehicles, top up.
    fatima = salik.register_account("Fatima Al Marri", "784-1990-1234567-1")
    salik.link_vehicle(fatima.emirates_id, Vehicle("DXB-A-12345", "Daily car"))
    salik.link_vehicle(fatima.emirates_id, Vehicle("DXB-B-67890", "Weekend car"))
    fatima.top_up(Decimal("100.00"), when=datetime(2026, 5, 4, 7, 0))

    # 2. Simulate a Monday's worth of passes.
    monday = datetime(2026, 5, 4)
    passes = [
        ("DXB-A-12345", Gate.AL_GARHOUD,     monday.replace(hour=7,  minute=45)),
        ("DXB-A-12345", Gate.AIRPORT_TUNNEL, monday.replace(hour=8,  minute=10)),
        ("DXB-B-67890", Gate.JEBEL_ALI,      monday.replace(hour=11, minute=30)),
        ("DXB-A-12345", Gate.BUSINESS_BAY,   monday.replace(hour=18, minute=5)),
        ("DXB-A-12345", Gate.AL_BARSHA,      monday.replace(hour=4,  minute=30)),
    ]
    print("Monday passes:")
    for plate, gate, when in passes:
        _print_tx(salik.pass_through(plate, gate, when))

    # 3. An unregistered plate triggers a fine.
    print("\nUnregistered vehicle pass:")
    _print_tx(salik.pass_through("AUH-Z-99999", Gate.AL_MAKTOUM,
                                  monday.replace(hour=9, minute=0)))

    # 4. Drain the account, then trigger an insufficient-balance fine.
    fatima.balance = Decimal("2.00")
    print("\nInsufficient balance pass (peak gate, only 2 AED on account):")
    _print_tx(salik.pass_through("DXB-A-12345", Gate.AL_MAMZAR_NORTH,
                                  monday.replace(hour=9, minute=30)))

    # 5. Low-balance alerts and full ledger.
    print("\nLow-balance alerts:")
    for acc in salik.low_balance_alerts():
        print(f"  {acc.holder_name}: AED {acc.balance}")

    print(f"\n{fatima.holder_name}'s ledger:")
    for tx in fatima.ledger:
        _print_tx(tx)


if __name__ == "__main__":
    main()
