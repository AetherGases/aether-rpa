from datetime import datetime

from permission_group import RegisterA, RegisterB, TableA, TableB
from permission_group.extractor import extract_from_a, extract_from_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


def test_register_b_and_table_b_hold_permission_group_fields() -> None:
    register = RegisterB(
        id=1,
        description="Administradores",
        created_at=CREATED_AT,
    )
    table = TableB(registers=[register])

    assert table.registers == [register]
    assert register.description == "Administradores"
    assert not hasattr(register, "updated_at")


def test_register_a_and_table_a_hold_permission_group_fields() -> None:
    register = RegisterA(
        id=1,
        description="Administradores",
        created_at=CREATED_AT,
    )
    table = TableA(registers=[register])

    assert table.registers == [register]
    assert register.description == "Administradores"
    assert not hasattr(register, "updated_at")


def test_table_b_accepts_empty_registers() -> None:
    table = TableB(registers=[])

    assert table.registers == []


def test_table_a_accepts_empty_registers() -> None:
    table = TableA(registers=[])

    assert table.registers == []


COLUMNS = ["id", "description", "created_at"]
SELECT_A = "SELECT id, description, created_at FROM permission_groups"
SELECT_B = "SELECT id, description, created_at FROM permission_group"
ROW = (1, "Administradores", CREATED_AT)


def test_extract_from_a_fills_register_a() -> None:
    connection, cursor = fake_connection(COLUMNS, [ROW])

    table = extract_from_a(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert table == TableA(
        registers=[RegisterA(id=1, description="Administradores", created_at=CREATED_AT)]
    )


def test_extract_from_b_fills_register_b() -> None:
    connection, cursor = fake_connection(COLUMNS, [ROW])

    table = extract_from_b(connection)

    cursor.execute.assert_called_once_with(SELECT_B)
    assert table == TableB(
        registers=[RegisterB(id=1, description="Administradores", created_at=CREATED_AT)]
    )


def test_extract_from_a_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS, [])

    assert extract_from_a(connection) == TableA(registers=[])


def test_extract_from_b_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS, [])

    assert extract_from_b(connection) == TableB(registers=[])


from permission_group.driver import drive_to_a, drive_to_b
from permission_group.transformer import transform_to_a, transform_to_b


def test_transform_to_b_copies_fields_from_a() -> None:
    connection, cursor = fake_connection(COLUMNS, [ROW])

    table = transform_to_b(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert table == TableB(
        registers=[RegisterB(id=1, description="Administradores", created_at=CREATED_AT)]
    )


def test_transform_to_a_copies_fields_from_b() -> None:
    connection, cursor = fake_connection(COLUMNS, [ROW])

    table = transform_to_a(connection)

    cursor.execute.assert_called_once_with(SELECT_B)
    assert table == TableA(
        registers=[RegisterA(id=1, description="Administradores", created_at=CREATED_AT)]
    )


def test_transform_to_b_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS, [])

    assert transform_to_b(connection) == TableB(registers=[])


def test_transform_to_a_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS, [])

    assert transform_to_a(connection) == TableA(registers=[])


def test_drive_to_b_insert_executemany() -> None:
    source_a, _source_cursor = fake_connection(COLUMNS, [ROW])
    dest_b, dest_cursor = fake_connection(COLUMNS, [])

    drive_to_b(source_a, dest_b, "insert")

    dest_cursor.executemany.assert_called_once_with(
        "INSERT INTO permission_group (id, description, created_at) VALUES (%s, %s, %s)",
        [(1, "Administradores", CREATED_AT)],
    )


def test_drive_to_a_update_executemany() -> None:
    dest_a, dest_cursor = fake_connection(COLUMNS, [])
    source_b, _source_cursor = fake_connection(COLUMNS, [ROW])

    drive_to_a(dest_a, source_b, "update")

    dest_cursor.executemany.assert_called_once_with(
        "UPDATE permission_groups SET description = %s, created_at = %s WHERE id = %s",
        [("Administradores", CREATED_AT, 1)],
    )


def test_drive_to_b_empty_source_does_not_executemany() -> None:
    source_a, _source_cursor = fake_connection(COLUMNS, [])
    dest_b, dest_cursor = fake_connection(COLUMNS, [])

    drive_to_b(source_a, dest_b, "insert")

    dest_cursor.executemany.assert_not_called()
