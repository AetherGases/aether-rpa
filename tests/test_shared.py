from dataclasses import dataclass
from enum import Enum

import pytest

from shared.driver import delete_rows, drive
from shared.extractor import extract
from shared.transformer import transform
from tests.fake_db import fake_connection


@dataclass
class _Register:
    id: int
    name: str


@dataclass
class _Table:
    registers: list[_Register]


QUERY = "SELECT id, name FROM items"


def test_extract_executes_query_and_fills_table() -> None:
    connection, cursor = fake_connection(["id", "name"], [(1, "alpha")])

    table = extract(connection, QUERY, _Register, _Table)

    cursor.execute.assert_called_once_with(QUERY)
    assert table == _Table(registers=[_Register(id=1, name="alpha")])


def test_extract_empty_rows_returns_empty_table() -> None:
    connection, _cursor = fake_connection(["id", "name"], [])

    table = extract(connection, QUERY, _Register, _Table)

    assert table == _Table(registers=[])


@dataclass
class _RegisterA:
    id: int
    name: str
    address_id: int | None


@dataclass
class _TableA:
    registers: list[_RegisterA]


@dataclass
class _RegisterB:
    id: int
    name: str
    id_address: int | None


@dataclass
class _TableB:
    registers: list[_RegisterB]


_FIELD_MAP = {"address_id": "id_address"}


def test_transform_remaps_named_fields_and_copies_the_rest() -> None:
    table = _TableA(registers=[_RegisterA(id=1, name="alpha", address_id=10)])

    result = transform(table, _RegisterB, _TableB, _FIELD_MAP)

    assert result == _TableB(registers=[_RegisterB(id=1, name="alpha", id_address=10)])


def test_transform_empty_registers_returns_empty_table() -> None:
    result = transform(_TableA(registers=[]), _RegisterB, _TableB, _FIELD_MAP)

    assert result == _TableB(registers=[])


def test_transform_applies_inverse_field_map() -> None:
    inverse = {target: source for source, target in _FIELD_MAP.items()}
    table = _TableB(registers=[_RegisterB(id=1, name="alpha", id_address=10)])

    result = transform(table, _RegisterA, _TableA, inverse)

    assert result == _TableA(registers=[_RegisterA(id=1, name="alpha", address_id=10)])


class _Status(Enum):
    ACTIVE = "ACTIVE"


@dataclass
class _DriveRegister:
    id: int
    name: str
    status: _Status | None = None


@dataclass
class _DriveTable:
    registers: list[_DriveRegister]


@dataclass
class _PkOnlyRegister:
    employee_id: int
    permission_group_id: int


@dataclass
class _PkOnlyTable:
    registers: list[_PkOnlyRegister]


def test_drive_insert_executemany_includes_pk() -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])

    drive(connection, table, "insert", "items", ("id",))

    cursor.executemany.assert_called_once_with(
        "INSERT INTO items (id, name, status) VALUES (%s, %s, %s)",
        [(1, "alpha", None)],
    )


def test_drive_update_sets_non_pk_where_pk() -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])

    drive(connection, table, "update", "items", ("id",))

    cursor.executemany.assert_called_once_with(
        "UPDATE items SET name = %s, status = %s WHERE id = %s",
        [("alpha", None, 1)],
    )


def test_drive_insert_converts_enum_to_value() -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    table = _DriveTable(
        registers=[_DriveRegister(id=1, name="alpha", status=_Status.ACTIVE)]
    )

    drive(connection, table, "insert", "items", ("id",))

    cursor.executemany.assert_called_once_with(
        "INSERT INTO items (id, name, status) VALUES (%s, %s, %s)",
        [(1, "alpha", "ACTIVE")],
    )


def test_drive_empty_registers_does_not_execute() -> None:
    connection, cursor = fake_connection(["id", "name"], [])

    drive(connection, _DriveTable(registers=[]), "insert", "items", ("id",))

    cursor.executemany.assert_not_called()
    connection.cursor.assert_not_called()


def test_drive_rejects_unknown_operation() -> None:
    connection, _cursor = fake_connection(["id", "name"], [])
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])

    with pytest.raises(ValueError):
        drive(connection, table, "merge", "items", ("id",))


def test_drive_update_with_only_pk_fields_does_not_execute() -> None:
    connection, cursor = fake_connection(["employee_id", "permission_group_id"], [])
    table = _PkOnlyTable(
        registers=[_PkOnlyRegister(employee_id=1, permission_group_id=2)]
    )

    drive(connection, table, "update", "permission_group_employees", ("employee_id", "permission_group_id"))

    cursor.executemany.assert_not_called()


def test_drive_delete_uses_pk_where() -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])
    drive(connection, table, "delete", "items", ("id",))
    cursor.executemany.assert_called_once_with(
        "DELETE FROM items WHERE id = %s",
        [(1,)],
    )


def test_drive_delete_composite_pk() -> None:
    connection, cursor = fake_connection(["employee_id", "permission_group_id"], [])
    table = _PkOnlyTable(
        registers=[_PkOnlyRegister(employee_id=1, permission_group_id=2)]
    )
    drive(
        connection,
        table,
        "delete",
        "permission_group_employees",
        ("employee_id", "permission_group_id"),
    )
    cursor.executemany.assert_called_once_with(
        "DELETE FROM permission_group_employees WHERE employee_id = %s AND permission_group_id = %s",
        [(1, 2)],
    )


def test_delete_rows_executemany() -> None:
    connection, cursor = fake_connection([], [])
    delete_rows(connection, "address", ("id",), [(1,), (2,)])
    cursor.executemany.assert_called_once_with(
        "DELETE FROM address WHERE id = %s",
        [(1,), (2,)],
    )


def test_delete_rows_empty_does_not_execute() -> None:
    connection, cursor = fake_connection([], [])
    delete_rows(connection, "address", ("id",), [])
    cursor.executemany.assert_not_called()
    connection.cursor.assert_not_called()
