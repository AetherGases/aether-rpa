from datetime import datetime

from storage_file import RegisterA, RegisterB, TableA, TableB
from storage_file.extractor import extract_from_a, extract_from_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


def test_register_b_and_table_b_hold_storage_file_fields() -> None:
    register = RegisterB(
        id=1,
        name="foto.png",
        path="/files/foto.png",
        created_at=CREATED_AT,
        updated_at=None,
    )
    table = TableB(registers=[register])

    assert table.registers == [register]
    assert register.name == "foto.png"
    assert register.path == "/files/foto.png"
    assert register.updated_at is None


def test_register_a_and_table_a_hold_storage_file_fields() -> None:
    register = RegisterA(
        id=1,
        name="foto.png",
        path="/files/foto.png",
        created_at=CREATED_AT,
        updated_at=None,
    )
    table = TableA(registers=[register])

    assert table.registers == [register]
    assert register.path == "/files/foto.png"


def test_table_b_accepts_empty_registers() -> None:
    table = TableB(registers=[])

    assert table.registers == []


def test_table_a_accepts_empty_registers() -> None:
    table = TableA(registers=[])

    assert table.registers == []


COLUMNS = ["id", "name", "path", "created_at", "updated_at"]
SELECT_A = "SELECT id, name, path, created_at, updated_at FROM storage_files"
SELECT_B = "SELECT id, name, path, created_at, updated_at FROM storage_file"
ROW = (1, "foto.png", "/files/foto.png", CREATED_AT, None)


def test_extract_from_a_fills_register_a() -> None:
    connection, cursor = fake_connection(COLUMNS, [ROW])

    table = extract_from_a(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert table == TableA(
        registers=[
            RegisterA(
                id=1,
                name="foto.png",
                path="/files/foto.png",
                created_at=CREATED_AT,
                updated_at=None,
            )
        ]
    )


def test_extract_from_b_fills_register_b() -> None:
    connection, cursor = fake_connection(COLUMNS, [ROW])

    table = extract_from_b(connection)

    cursor.execute.assert_called_once_with(SELECT_B)
    assert table == TableB(
        registers=[
            RegisterB(
                id=1,
                name="foto.png",
                path="/files/foto.png",
                created_at=CREATED_AT,
                updated_at=None,
            )
        ]
    )


def test_extract_from_a_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS, [])

    assert extract_from_a(connection) == TableA(registers=[])


def test_extract_from_b_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS, [])

    assert extract_from_b(connection) == TableB(registers=[])
