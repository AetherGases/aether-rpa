from datetime import datetime

from department import RegisterA, RegisterB, TableA, TableB
from department.driver import drive_to_a, drive_to_b
from department.extractor import extract_from_a, extract_from_b
from department.transformer import transform_to_a, transform_to_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


def test_register_b_and_table_b_hold_department_fields() -> None:
    register = RegisterB(
        id=1,
        name="Operacoes",
        description=None,
        created_at=CREATED_AT,
        updated_at=None,
        id_unit=None,
    )
    table = TableB(registers=[register])

    assert table.registers == [register]
    assert register.name == "Operacoes"
    assert register.description is None
    assert register.id_unit is None


def test_register_a_and_table_a_hold_sector_fields() -> None:
    register = RegisterA(
        id=1,
        name="Operacoes",
        description=None,
        created_at=CREATED_AT,
        updated_at=None,
        unit_id=None,
    )
    table = TableA(registers=[register])

    assert table.registers == [register]
    assert register.unit_id is None
    assert not hasattr(register, "id_unit")


def test_table_b_accepts_empty_registers() -> None:
    table = TableB(registers=[])

    assert table.registers == []


def test_table_a_accepts_empty_registers() -> None:
    table = TableA(registers=[])

    assert table.registers == []


COLUMNS_A = ["id", "name", "description", "created_at", "updated_at", "unit_id"]
COLUMNS_B = ["id", "name", "description", "created_at", "updated_at", "id_unit"]
SELECT_A = "SELECT id, name, description, created_at, updated_at, unit_id FROM sectors"
SELECT_B = "SELECT id, name, description, created_at, updated_at, id_unit FROM department"
ROW = (1, "Operacoes", None, CREATED_AT, None, 4)


def test_extract_from_a_fills_register_a() -> None:
    connection, cursor = fake_connection(COLUMNS_A, [ROW])

    table = extract_from_a(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert table == TableA(
        registers=[
            RegisterA(
                id=1,
                name="Operacoes",
                description=None,
                created_at=CREATED_AT,
                updated_at=None,
                unit_id=4,
            )
        ]
    )


def test_extract_from_b_fills_register_b() -> None:
    connection, cursor = fake_connection(COLUMNS_B, [ROW])

    table = extract_from_b(connection)

    cursor.execute.assert_called_once_with(SELECT_B)
    assert table == TableB(
        registers=[
            RegisterB(
                id=1,
                name="Operacoes",
                description=None,
                created_at=CREATED_AT,
                updated_at=None,
                id_unit=4,
            )
        ]
    )


def test_extract_from_a_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_A, [])

    assert extract_from_a(connection) == TableA(registers=[])


def test_extract_from_b_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_B, [])

    assert extract_from_b(connection) == TableB(registers=[])


def test_transform_to_b_remaps_unit_id() -> None:
    connection, cursor = fake_connection(COLUMNS_A, [ROW])

    result = transform_to_b(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert result == TableB(
        registers=[
            RegisterB(
                id=1,
                name="Operacoes",
                description=None,
                created_at=CREATED_AT,
                updated_at=None,
                id_unit=4,
            )
        ]
    )


def test_transform_to_a_remaps_id_unit() -> None:
    connection, cursor = fake_connection(COLUMNS_B, [ROW])

    result = transform_to_a(connection)

    cursor.execute.assert_called_once_with(SELECT_B)
    assert result == TableA(
        registers=[
            RegisterA(
                id=1,
                name="Operacoes",
                description=None,
                created_at=CREATED_AT,
                updated_at=None,
                unit_id=4,
            )
        ]
    )


def test_transform_to_b_empty_registers() -> None:
    connection, _cursor = fake_connection(COLUMNS_A, [])

    assert transform_to_b(connection) == TableB(registers=[])


def test_transform_to_a_empty_registers() -> None:
    connection, _cursor = fake_connection(COLUMNS_B, [])

    assert transform_to_a(connection) == TableA(registers=[])


def test_drive_to_b_insert_executemany_on_connection_b() -> None:
    connection_a, _cursor_a = fake_connection(COLUMNS_A, [ROW])
    connection_b, cursor_b = fake_connection(COLUMNS_B, [])

    drive_to_b(connection_a, connection_b, "insert")

    cursor_b.executemany.assert_called_once_with(
        "INSERT INTO department (id, name, description, created_at, updated_at, id_unit) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        [(1, "Operacoes", None, CREATED_AT, None, 4)],
    )


def test_drive_to_a_update_executemany_on_connection_a() -> None:
    connection_a, cursor_a = fake_connection(COLUMNS_A, [])
    connection_b, _cursor_b = fake_connection(COLUMNS_B, [ROW])

    drive_to_a(connection_a, connection_b, "update")

    cursor_a.executemany.assert_called_once_with(
        "UPDATE sectors SET name = %s, description = %s, created_at = %s, updated_at = %s, "
        "unit_id = %s WHERE id = %s",
        [("Operacoes", None, CREATED_AT, None, 4, 1)],
    )


def test_drive_to_b_empty_registers_does_not_execute() -> None:
    connection_a, _cursor_a = fake_connection(COLUMNS_A, [])
    connection_b, cursor_b = fake_connection(COLUMNS_B, [])

    drive_to_b(connection_a, connection_b, "insert")

    cursor_b.executemany.assert_not_called()
    connection_b.cursor.assert_not_called()
