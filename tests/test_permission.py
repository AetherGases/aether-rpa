from datetime import datetime

from permission import Register, Table


def test_register_and_table_hold_permission_fields() -> None:
    created_at = datetime(2026, 9, 12, 14, 0, 0)
    register = Register(
        id=1,
        name="visualizar_dashboard",
        description=None,
        url="/dashboard",
        created_at=created_at,
        updated_at=None,
    )
    table = Table(registers=[register])

    assert table.registers == [register]
    assert register.name == "visualizar_dashboard"
    assert register.description is None
    assert register.url == "/dashboard"


def test_table_accepts_empty_registers() -> None:
    table = Table(registers=[])

    assert table.registers == []
