from datetime import datetime

from permission_group import Register, Table


def test_register_and_table_hold_permission_group_fields() -> None:
    created_at = datetime(2026, 9, 12, 14, 0, 0)
    register = Register(
        id=1,
        description="Administradores",
        created_at=created_at,
    )
    table = Table(registers=[register])

    assert table.registers == [register]
    assert register.description == "Administradores"
    assert not hasattr(register, "updated_at")


def test_table_accepts_empty_registers() -> None:
    table = Table(registers=[])

    assert table.registers == []
