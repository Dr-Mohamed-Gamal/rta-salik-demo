"""Fine schedule and per-plate violation tracking."""

from decimal import Decimal


# Per-offence fines and the published annual cap.
FINE_SCHEDULE = [Decimal("100"), Decimal("200"), Decimal("400")]
ANNUAL_FINE_CAP = Decimal("10000")


class ViolationRegistry:
    """Tracks fines per plate. Escalates and respects the annual cap."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}
        self._totals: dict[str, Decimal] = {}

    def record(self, plate: str) -> Decimal:
        n = self._counts.get(plate, 0)
        fine = FINE_SCHEDULE[min(n, len(FINE_SCHEDULE) - 1)]
        running = self._totals.get(plate, Decimal("0"))
        if running + fine > ANNUAL_FINE_CAP:
            fine = max(Decimal("0"), ANNUAL_FINE_CAP - running)
        self._counts[plate] = n + 1
        self._totals[plate] = running + fine
        return fine

    def total_for(self, plate: str) -> Decimal:
        return self._totals.get(plate, Decimal("0"))

    def count_for(self, plate: str) -> int:
        return self._counts.get(plate, 0)
