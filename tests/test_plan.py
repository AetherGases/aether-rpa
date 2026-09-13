from datetime import datetime
from decimal import Decimal

from plan import Register, Table


def test_register_and_table_hold_plan_fields() -> None:
    created_at = datetime(2026, 9, 12, 14, 0, 0)
    register = Register(
        id=1,
        name="Pro",
        description=None,
        price=Decimal("99.90"),
        duration_days=30,
        is_active=True,
        created_at=created_at,
        updated_at=None,
    )
    table = Table(registers=[register])

    assert table.registers == [register]
    assert register.price == Decimal("99.90")
    assert register.description is None
    assert register.duration_days == 30


def test_table_accepts_empty_registers() -> None:
    table = Table(registers=[])

    assert table.registers == []
