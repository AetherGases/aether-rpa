from datetime import datetime

from permission_group_permission import Register, Table


def test_register_and_table_hold_permission_group_permission_fields() -> None:
    created_at = datetime(2026, 9, 12, 14, 0, 0)
    register = Register(
        id=1,
        created_at=created_at,
        updated_at=None,
        id_permission=None,
        id_permission_group=None,
    )
    table = Table(registers=[register])

    assert table.registers == [register]
    assert register.id_permission is None
    assert register.id_permission_group is None


def test_table_accepts_empty_registers() -> None:
    table = Table(registers=[])

    assert table.registers == []
