from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from unittest.mock import patch

import pytest

from src.definition import (
    AddressA,
    AddressB,
    AddressTableA,
    AddressTableB,
    EmployeeB,
    EmployeeStatus,
    EmployeeTableB,
    PermissionGroupEmployeeB,
    PermissionGroupEmployeeTableB,
)
from src.driver import delete_rows, drive, drive_to_a, drive_to_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


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
        "INSERT INTO items (id, name, status) VALUES (%s, %s, %s) "
        "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, status = EXCLUDED.status",
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
        "INSERT INTO items (id, name, status) VALUES (%s, %s, %s) "
        "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, status = EXCLUDED.status",
        [(1, "alpha", "ACTIVE")],
    )


def test_drive_empty_registers_does_not_execute() -> None:
    connection, cursor = fake_connection(["id", "name"], [])

    drive(connection, _DriveTable(registers=[]), "insert", "items", ("id",))

    cursor.executemany.assert_not_called()
    connection.cursor.assert_not_called()


def test_drive_insert_pk_only_does_nothing_on_conflict() -> None:
    connection, cursor = fake_connection(["employee_id", "permission_group_id"], [])
    table = _PkOnlyTable(
        registers=[_PkOnlyRegister(employee_id=1, permission_group_id=2)]
    )

    drive(
        connection,
        table,
        "insert",
        "permission_group_employees",
        ("employee_id", "permission_group_id"),
    )

    cursor.executemany.assert_called_once_with(
        "INSERT INTO permission_group_employees (employee_id, permission_group_id) "
        "VALUES (%s, %s) ON CONFLICT (employee_id, permission_group_id) DO NOTHING",
        [(1, 2)],
    )


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

    drive(
        connection,
        table,
        "update",
        "permission_group_employees",
        ("employee_id", "permission_group_id"),
    )

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


def _address_b() -> AddressB:
    return AddressB(
        id=1,
        zip_code="01310100",
        state="SP",
        city="Sao Paulo",
        neighborhood="Bela Vista",
        street="Avenida Paulista",
        number=1000,
        complement=None,
        created_at=CREATED_AT,
        updated_at=None,
    )


def _address_a() -> AddressA:
    return AddressA(
        id=1,
        zip_code="01310100",
        state="SP",
        city="Sao Paulo",
        neighborhood="Bela Vista",
        street="Avenida Paulista",
        number=1000,
        complement=None,
        created_at=CREATED_AT,
        updated_at=None,
    )


def test_drive_to_b_addresses_insert() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, cursor_b = fake_connection([], [])
    table = AddressTableB(registers=[_address_b()])

    with patch("src.driver.transform_to_b", return_value=table) as transform:
        drive_to_b(connection_a, connection_b, "insert", "addresses")

    transform.assert_called_once_with(connection_a, "addresses")
    cursor_b.executemany.assert_called_once_with(
        "INSERT INTO address (id, zip_code, state, city, neighborhood, street, number, complement, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (id) DO UPDATE SET zip_code = EXCLUDED.zip_code, state = EXCLUDED.state, city = EXCLUDED.city, neighborhood = EXCLUDED.neighborhood, street = EXCLUDED.street, number = EXCLUDED.number, complement = EXCLUDED.complement, created_at = EXCLUDED.created_at, updated_at = EXCLUDED.updated_at",
        [
            (
                1,
                "01310100",
                "SP",
                "Sao Paulo",
                "Bela Vista",
                "Avenida Paulista",
                1000,
                None,
                CREATED_AT,
                None,
            )
        ],
    )


def test_drive_to_a_addresses_update() -> None:
    connection_a, cursor_a = fake_connection([], [])
    connection_b, _cursor_b = fake_connection([], [])
    table = AddressTableA(registers=[_address_a()])

    with patch("src.driver.transform_to_a", return_value=table) as transform:
        drive_to_a(connection_a, connection_b, "update", "addresses")

    transform.assert_called_once_with(connection_b, "addresses")
    cursor_a.executemany.assert_called_once_with(
        "UPDATE addresses SET zip_code = %s, state = %s, city = %s, neighborhood = %s, street = %s, number = %s, complement = %s, created_at = %s, updated_at = %s WHERE id = %s",
        [
            (
                "01310100",
                "SP",
                "Sao Paulo",
                "Bela Vista",
                "Avenida Paulista",
                1000,
                None,
                CREATED_AT,
                None,
                1,
            )
        ],
    )


def test_drive_to_b_employees_insert_converts_enum_to_string() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, cursor_b = fake_connection([], [])
    table = EmployeeTableB(
        registers=[
            EmployeeB(
                id=1,
                cpf="12345678901",
                name="Ana Silva",
                email="ana@example.com",
                phone="11999999999",
                password_hash="hash",
                employee_status=EmployeeStatus.ACTIVE,
                created_at=CREATED_AT,
                updated_at=None,
                id_storage_file=5,
                id_department=6,
            )
        ]
    )

    with patch("src.driver.transform_to_b", return_value=table) as transform:
        drive_to_b(connection_a, connection_b, "insert", "employees")

    transform.assert_called_once_with(connection_a, "employees")
    cursor_b.executemany.assert_called_once_with(
        "INSERT INTO employee (id, cpf, name, email, phone, password_hash, "
        "employee_status, created_at, updated_at, id_storage_file, id_department) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (id) DO UPDATE SET cpf = EXCLUDED.cpf, name = EXCLUDED.name, "
        "email = EXCLUDED.email, phone = EXCLUDED.phone, password_hash = EXCLUDED.password_hash, "
        "employee_status = EXCLUDED.employee_status, created_at = EXCLUDED.created_at, "
        "updated_at = EXCLUDED.updated_at, id_storage_file = EXCLUDED.id_storage_file, "
        "id_department = EXCLUDED.id_department",
        [
            (
                1,
                "12345678901",
                "Ana Silva",
                "ana@example.com",
                "11999999999",
                "hash",
                "ACTIVE",
                CREATED_AT,
                None,
                5,
                6,
            )
        ],
    )


def test_drive_to_b_permission_group_employees_update_does_not_executemany() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, cursor_b = fake_connection([], [])
    table = PermissionGroupEmployeeTableB(
        registers=[
            PermissionGroupEmployeeB(id_employee=1, id_permission_group=2)
        ]
    )

    with patch("src.driver.transform_to_b", return_value=table) as transform:
        drive_to_b(connection_a, connection_b, "update", "permission_group_employees")

    transform.assert_called_once_with(connection_a, "permission_group_employees")
    cursor_b.executemany.assert_not_called()
    connection_b.cursor.assert_not_called()


def test_drive_to_b_empty_source_does_not_executemany() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, cursor_b = fake_connection([], [])
    table = AddressTableB(registers=[])

    with patch("src.driver.transform_to_b", return_value=table) as transform:
        drive_to_b(connection_a, connection_b, "insert", "addresses")

    transform.assert_called_once_with(connection_a, "addresses")
    cursor_b.executemany.assert_not_called()
    connection_b.cursor.assert_not_called()


def test_drive_to_b_delete_uses_row_pks_and_skips_transform() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, cursor_b = fake_connection([], [])

    with patch("src.driver.transform_to_b") as transform:
        drive_to_b(
            connection_a,
            connection_b,
            "delete",
            "addresses",
            row_pks=[{"id": 1}, {"id": 2}],
        )

    transform.assert_not_called()
    connection_a.cursor.assert_not_called()
    cursor_b.executemany.assert_called_once_with(
        "DELETE FROM address WHERE id = %s",
        [(1,), (2,)],
    )


def test_drive_to_b_delete_maps_composite_pk() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, cursor_b = fake_connection([], [])

    drive_to_b(
        connection_a,
        connection_b,
        "delete",
        "permission_group_employees",
        row_pks=[{"employee_id": 1, "permission_group_id": 2}],
    )

    cursor_b.executemany.assert_called_once_with(
        "DELETE FROM permission_group_employee "
        "WHERE id_employee = %s AND id_permission_group = %s",
        [(1, 2)],
    )


def test_drive_to_a_delete_uses_row_pks_and_skips_transform() -> None:
    connection_a, cursor_a = fake_connection([], [])
    connection_b, _cursor_b = fake_connection([], [])

    with patch("src.driver.transform_to_a") as transform:
        drive_to_a(
            connection_a,
            connection_b,
            "delete",
            "addresses",
            row_pks=[{"id": 4}],
        )

    transform.assert_not_called()
    connection_b.cursor.assert_not_called()
    cursor_a.executemany.assert_called_once_with(
        "DELETE FROM addresses WHERE id = %s",
        [(4,)],
    )


def test_drive_to_b_delete_empty_row_pks_does_not_execute() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, cursor_b = fake_connection([], [])

    drive_to_b(connection_a, connection_b, "delete", "addresses", row_pks=[])

    cursor_b.executemany.assert_not_called()
    connection_b.cursor.assert_not_called()
    connection_a.cursor.assert_not_called()
