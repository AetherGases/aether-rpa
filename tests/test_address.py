from datetime import datetime

from address import Register, Table


def test_register_and_table_hold_address_fields() -> None:
    created_at = datetime(2026, 9, 12, 14, 0, 0)
    register = Register(
        id=1,
        zip_code="01310100",
        state="SP",
        city="Sao Paulo",
        neighborhood="Bela Vista",
        street="Avenida Paulista",
        number=1000,
        complement=None,
        created_at=created_at,
        updated_at=None,
    )
    table = Table(registers=[register])

    assert table.registers == [register]
    assert register.zip_code == "01310100"
    assert register.complement is None
    assert register.updated_at is None


def test_table_accepts_empty_registers() -> None:
    table = Table(registers=[])

    assert table.registers == []
