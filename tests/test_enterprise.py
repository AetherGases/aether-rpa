from datetime import datetime

from enterprise import Register, Table


def test_register_and_table_hold_enterprise_fields() -> None:
    created_at = datetime(2026, 9, 12, 14, 0, 0)
    register = Register(
        id=1,
        name="Aether Ltda",
        trade_name=None,
        cnpj="12345678901234",
        created_at=created_at,
        updated_at=None,
        id_address=None,
    )
    table = Table(registers=[register])

    assert table.registers == [register]
    assert register.name == "Aether Ltda"
    assert register.trade_name is None
    assert register.id_address is None


def test_table_accepts_empty_registers() -> None:
    table = Table(registers=[])

    assert table.registers == []
