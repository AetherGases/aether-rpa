from datetime import datetime

from department import Register, Table


def test_register_and_table_hold_department_fields() -> None:
    created_at = datetime(2026, 9, 12, 14, 0, 0)
    register = Register(
        id=1,
        name="Operacoes",
        description=None,
        created_at=created_at,
        updated_at=None,
        id_unit=None,
    )
    table = Table(registers=[register])

    assert table.registers == [register]
    assert register.name == "Operacoes"
    assert register.description is None
    assert register.id_unit is None


def test_table_accepts_empty_registers() -> None:
    table = Table(registers=[])

    assert table.registers == []
