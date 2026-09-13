from datetime import datetime

from unit import Register, Table


def test_register_and_table_hold_unit_fields() -> None:
    created_at = datetime(2026, 9, 12, 14, 0, 0)
    register = Register(
        id=1,
        cnae=None,
        cnpj="12345678901234",
        is_active=True,
        created_at=created_at,
        updated_at=None,
        id_enterprise=None,
        id_address=None,
    )
    table = Table(registers=[register])

    assert table.registers == [register]
    assert register.is_active is True
    assert register.cnae is None
    assert register.id_enterprise is None


def test_table_accepts_empty_registers() -> None:
    table = Table(registers=[])

    assert table.registers == []
