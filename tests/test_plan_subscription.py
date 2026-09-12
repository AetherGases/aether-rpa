from datetime import datetime

from plan_subscription import Register, Table


def test_register_and_table_hold_plan_subscription_fields() -> None:
    created_at = datetime(2026, 9, 12, 14, 0, 0)
    register = Register(
        id=1,
        is_active=True,
        installments=12,
        created_at=created_at,
        deactivated_at=None,
        id_plan=None,
        id_enterprise=None,
    )
    table = Table(registers=[register])

    assert table.registers == [register]
    assert register.installments == 12
    assert register.deactivated_at is None
    assert register.id_plan is None


def test_table_accepts_empty_registers() -> None:
    table = Table(registers=[])

    assert table.registers == []
