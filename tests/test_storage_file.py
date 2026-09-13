from datetime import datetime

from storage_file import Register, Table


def test_register_and_table_hold_storage_file_fields() -> None:
    created_at = datetime(2026, 9, 12, 14, 0, 0)
    register = Register(
        id=1,
        name="foto.png",
        path="/files/foto.png",
        created_at=created_at,
        updated_at=None,
    )
    table = Table(registers=[register])

    assert table.registers == [register]
    assert register.name == "foto.png"
    assert register.path == "/files/foto.png"
    assert register.updated_at is None


def test_table_accepts_empty_registers() -> None:
    table = Table(registers=[])

    assert table.registers == []
