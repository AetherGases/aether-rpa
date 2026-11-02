import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from unittest.mock import call, patch

import psycopg2
import pytest

from src.definition import (
    TABLES,
    AddressA,
    AddressB,
    AddressTableA,
    AddressTableB,
    EmployeeB,
    PlanSubscriptionB,
    PlanSubscriptionTableB,
    StatusEmployee,
    EmployeeTableB,
)
from src.driver import delete_rows, drive, drive_to_a, drive_to_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)
SAVEPOINT = call("SAVEPOINT rpa_isolate")
RELEASE = call("RELEASE SAVEPOINT rpa_isolate")
ROLLBACK_TO = call("ROLLBACK TO SAVEPOINT rpa_isolate")


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


def _upserts(cursor) -> list[tuple]:
    return [
        c.args
        for c in cursor.execute.call_args_list
        if c.args[0].startswith("INSERT")
    ]


def _no_sequence(cursor) -> None:
    cursor.fetchone.return_value = (None,)


def _fail_row(cursor, error: Exception, row_id: int) -> None:
    def execute(sql, params=None):
        if sql.startswith("INSERT") and params[0] == row_id:
            raise error

    cursor.execute.side_effect = execute


def test_drive_insert_upserts_each_row_inside_a_savepoint() -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    _no_sequence(cursor)
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])

    drive(connection, table, "insert", "items", ("id",))

    query = (
        "INSERT INTO items (id, name, status) VALUES (%s, %s, %s) "
        "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, status = EXCLUDED.status"
    )
    assert cursor.execute.call_args_list[:3] == [
        SAVEPOINT,
        call(query, (1, "alpha", None)),
        RELEASE,
    ]


def test_drive_update_is_the_same_upsert_as_insert() -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    _no_sequence(cursor)
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])

    drive(connection, table, "update", "items", ("id",))

    assert _upserts(cursor) == [
        (
            "INSERT INTO items (id, name, status) VALUES (%s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, status = EXCLUDED.status",
            (1, "alpha", None),
        )
    ]


def test_drive_insert_converts_enum_to_value() -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    _no_sequence(cursor)
    table = _DriveTable(
        registers=[_DriveRegister(id=1, name="alpha", status=_Status.ACTIVE)]
    )

    drive(connection, table, "insert", "items", ("id",))

    assert _upserts(cursor)[0][1] == (1, "alpha", "ACTIVE")


def test_drive_conflict_exprs_replace_excluded_value() -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    _no_sequence(cursor)
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])

    drive(
        connection,
        table,
        "insert",
        "items",
        ("id",),
        conflict_exprs={"name": "COALESCE(EXCLUDED.name, items.name)"},
    )

    assert _upserts(cursor)[0][0] == (
        "INSERT INTO items (id, name, status) VALUES (%s, %s, %s) "
        "ON CONFLICT (id) DO UPDATE SET name = COALESCE(EXCLUDED.name, items.name), "
        "status = EXCLUDED.status"
    )


def test_drive_empty_registers_does_not_execute() -> None:
    connection, cursor = fake_connection(["id", "name"], [])

    drive(connection, _DriveTable(registers=[]), "insert", "items", ("id",))

    cursor.execute.assert_not_called()
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
        "link_table",
        ("employee_id", "permission_group_id"),
    )

    assert _upserts(cursor) == [
        (
            "INSERT INTO link_table (employee_id, permission_group_id) "
            "VALUES (%s, %s) ON CONFLICT (employee_id, permission_group_id) DO NOTHING",
            (1, 2),
        )
    ]


def test_drive_composite_pk_does_not_touch_sequences() -> None:
    connection, cursor = fake_connection(["employee_id", "permission_group_id"], [])
    table = _PkOnlyTable(
        registers=[_PkOnlyRegister(employee_id=1, permission_group_id=2)]
    )

    drive(connection, table, "update", "link_table", ("employee_id", "permission_group_id"))

    assert not any("pg_get_serial_sequence" in c.args[0] for c in cursor.execute.call_args_list)


def test_drive_rejects_unknown_operation() -> None:
    connection, _cursor = fake_connection(["id", "name"], [])
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])

    with pytest.raises(ValueError):
        drive(connection, table, "merge", "items", ("id",))


def test_drive_skips_a_bad_row_logs_it_and_keeps_the_others(caplog) -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    _no_sequence(cursor)
    _fail_row(cursor, psycopg2.errors.StringDataRightTruncation("too long"), 2)
    table = _DriveTable(
        registers=[
            _DriveRegister(id=1, name="ok"),
            _DriveRegister(id=2, name="bad"),
            _DriveRegister(id=3, name="ok too"),
        ]
    )

    with caplog.at_level(logging.ERROR, logger="aether.rpa"):
        drive(connection, table, "insert", "items", ("id",))

    assert [args[1][0] for args in _upserts(cursor)] == [1, 2, 3]
    assert ROLLBACK_TO in cursor.execute.call_args_list
    assert cursor.execute.call_args_list.count(RELEASE) >= 2
    assert "RPA skipped items row (2,)" in caplog.text
    assert "StringDataRightTruncation" in caplog.text


@pytest.mark.parametrize(
    "error",
    [
        psycopg2.errors.CheckViolation("department must resolve to an enterprise"),
        psycopg2.errors.NotNullViolation("null value"),
        psycopg2.errors.ForeignKeyViolation("fk"),
        psycopg2.errors.UniqueViolation("duplicate"),
    ],
)
def test_drive_isolates_integrity_errors(error: Exception) -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    _no_sequence(cursor)
    _fail_row(cursor, error, 1)
    table = _DriveTable(registers=[_DriveRegister(id=1, name="bad")])

    drive(connection, table, "insert", "items", ("id",))

    assert ROLLBACK_TO in cursor.execute.call_args_list


def test_drive_does_not_swallow_connection_errors() -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    _fail_row(cursor, psycopg2.OperationalError("connection lost"), 1)
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])

    with pytest.raises(psycopg2.OperationalError):
        drive(connection, table, "insert", "items", ("id",))


def test_drive_moves_the_sequence_past_the_copied_ids() -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    cursor.fetchone.return_value = ("public.items_id_seq",)
    table = _DriveTable(registers=[_DriveRegister(id=10001, name="alpha")])

    drive(connection, table, "insert", "items", ("id",))

    assert call("SELECT pg_get_serial_sequence(%s, %s)", ("items", "id")) in (
        cursor.execute.call_args_list
    )
    assert call(
        "SELECT setval(%s, GREATEST("
        "(SELECT COALESCE(MAX(id), 1) FROM items), "
        "(SELECT last_value FROM public.items_id_seq)))",
        ("public.items_id_seq",),
    ) in cursor.execute.call_args_list


def test_drive_without_a_sequence_does_not_call_setval() -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    _no_sequence(cursor)
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])

    drive(connection, table, "insert", "items", ("id",))

    assert not any("setval" in c.args[0] for c in cursor.execute.call_args_list)


def test_drive_sequence_failure_is_a_warning_not_an_error(caplog) -> None:
    connection, cursor = fake_connection(["id", "name"], [])

    def execute(sql, params=None):
        if "pg_get_serial_sequence" in sql:
            raise psycopg2.errors.InsufficientPrivilege("permission denied")

    cursor.execute.side_effect = execute
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])

    with caplog.at_level(logging.WARNING, logger="aether.rpa"):
        drive(connection, table, "insert", "items", ("id",))

    assert "could not advance the items.id sequence" in caplog.text
    assert cursor.execute.call_args_list[-1] == ROLLBACK_TO


def test_drive_update_with_only_pk_fields_is_an_upsert_do_nothing() -> None:
    connection, cursor = fake_connection(["employee_id", "permission_group_id"], [])
    table = _PkOnlyTable(
        registers=[_PkOnlyRegister(employee_id=1, permission_group_id=2)]
    )

    drive(
        connection,
        table,
        "update",
        "link_table",
        ("employee_id", "permission_group_id"),
    )

    assert "DO NOTHING" in _upserts(cursor)[0][0]


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
        "link_table",
        ("employee_id", "permission_group_id"),
    )

    cursor.executemany.assert_called_once_with(
        "DELETE FROM link_table WHERE employee_id = %s AND permission_group_id = %s",
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
        number="1000",
        complement=None,
        created_at=CREATED_AT,
        updated_at=None,
    )


def test_drive_to_b_addresses_insert() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, cursor_b = fake_connection([], [])
    _no_sequence(cursor_b)
    table = AddressTableB(registers=[_address_b()])

    with patch("src.driver.transform_to_b", return_value=table) as transform:
        drive_to_b(connection_a, connection_b, "insert", "addresses")

    transform.assert_called_once_with(connection_a, "addresses", pks=None)
    assert _upserts(cursor_b) == [
        (
            "INSERT INTO address (id, zip_code, state, city, neighborhood, street, number, complement, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET zip_code = EXCLUDED.zip_code, state = EXCLUDED.state, city = EXCLUDED.city, neighborhood = EXCLUDED.neighborhood, street = EXCLUDED.street, number = EXCLUDED.number, complement = EXCLUDED.complement, created_at = EXCLUDED.created_at, updated_at = EXCLUDED.updated_at",
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
            ),
        )
    ]


def test_drive_to_b_restricts_extraction_to_outbox_ids() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, _cursor_b = fake_connection([], [])

    with patch(
        "src.driver.transform_to_b", return_value=AddressTableB(registers=[])
    ) as transform:
        drive_to_b(
            connection_a,
            connection_b,
            "insert",
            "addresses",
            row_pks=[{"id": 4}, {"id": 7}],
        )

    transform.assert_called_once_with(connection_a, "addresses", pks=[4, 7])


def test_drive_to_a_addresses_update_keeps_a_text_cut_in_b() -> None:
    connection_a, cursor_a = fake_connection([], [])
    connection_b, _cursor_b = fake_connection([], [])
    _no_sequence(cursor_a)
    table = AddressTableA(registers=[_address_a()])

    with patch("src.driver.transform_to_a", return_value=table) as transform:
        drive_to_a(connection_a, connection_b, "update", "addresses")

    transform.assert_called_once_with(connection_b, "addresses", pks=None)
    query, row = _upserts(cursor_a)[0]
    assert query.startswith("INSERT INTO addresses (id, zip_code, state, ")
    assert (
        "street = CASE WHEN left(addresses.street, 150) = EXCLUDED.street "
        "THEN addresses.street ELSE EXCLUDED.street END"
    ) in query
    assert "number = CASE WHEN (CASE WHEN length(substring(addresses.number" in query
    assert row == (
        1,
        "01310100",
        "SP",
        "Sao Paulo",
        "Bela Vista",
        "Avenida Paulista",
        "1000",
        None,
        CREATED_AT,
        None,
    )


def test_drive_to_a_restricts_extraction_to_outbox_ids() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, _cursor_b = fake_connection([], [])

    with patch(
        "src.driver.transform_to_a", return_value=AddressTableA(registers=[])
    ) as transform:
        drive_to_a(
            connection_a, connection_b, "update", "addresses", row_pks=[{"id": 9}]
        )

    transform.assert_called_once_with(connection_b, "addresses", pks=[9])


def _employee_b() -> EmployeeB:
    return EmployeeB(
        id=1,
        cpf="12345678901",
        name="Ana Silva",
        email="ana@example.com",
        phone="11999999999",
        password_hash="hash",
        employee_status=StatusEmployee.ACTIVE,
        created_at=CREATED_AT,
        updated_at=None,
        id_storage_file=5,
        id_department=6,
        id_permission_group=2,
        company_id=3,
        unit_id=4,
    )


def test_drive_to_b_employees_never_writes_derived_company_and_unit() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, cursor_b = fake_connection([], [])
    _no_sequence(cursor_b)
    table = EmployeeTableB(registers=[_employee_b()])

    with patch("src.driver.transform_to_b", return_value=table) as transform:
        drive_to_b(connection_a, connection_b, "insert", "employees")

    transform.assert_called_once_with(connection_a, "employees", pks=None)
    assert _upserts(cursor_b) == [
        (
            "INSERT INTO employee (id, cpf, name, email, phone, password_hash, "
            "employee_status, created_at, updated_at, id_storage_file, id_department, "
            "id_permission_group) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET cpf = EXCLUDED.cpf, name = EXCLUDED.name, "
            "email = EXCLUDED.email, phone = EXCLUDED.phone, password_hash = EXCLUDED.password_hash, "
            "employee_status = EXCLUDED.employee_status, created_at = EXCLUDED.created_at, "
            "updated_at = EXCLUDED.updated_at, id_storage_file = EXCLUDED.id_storage_file, "
            "id_department = EXCLUDED.id_department, id_permission_group = EXCLUDED.id_permission_group",
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
                2,
            ),
        )
    ]


def test_drive_to_b_subscriptions_never_shrinks_installments_above_one() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, cursor_b = fake_connection([], [])
    _no_sequence(cursor_b)
    table = PlanSubscriptionTableB(
        registers=[
            PlanSubscriptionB(
                id=1,
                is_active=True,
                installments=1,
                created_at=CREATED_AT,
                deactivated_at=None,
                id_plan=1,
                id_enterprise=1,
            )
        ]
    )

    with patch("src.driver.transform_to_b", return_value=table):
        drive_to_b(connection_a, connection_b, "update", "subscriptions")

    assert (
        "installments = CASE WHEN EXCLUDED.installments > 0 AND "
        "plan_subscription.installments > 0 THEN plan_subscription.installments "
        "ELSE EXCLUDED.installments END"
    ) in _upserts(cursor_b)[0][0]


def test_drive_to_b_empty_source_does_not_execute() -> None:
    connection_a, _cursor_a = fake_connection([], [])
    connection_b, cursor_b = fake_connection([], [])
    table = AddressTableB(registers=[])

    with patch("src.driver.transform_to_b", return_value=table) as transform:
        drive_to_b(connection_a, connection_b, "insert", "addresses")

    transform.assert_called_once_with(connection_a, "addresses", pks=None)
    cursor_b.execute.assert_not_called()
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


def test_every_conflict_expression_targets_its_own_table() -> None:
    for spec in TABLES.values():
        for column, expr in spec.conflict_a.items():
            assert f"EXCLUDED.{column}" in expr
            assert spec.table_name_a in expr
        for column, expr in spec.conflict_b.items():
            assert f"EXCLUDED.{column}" in expr
            assert spec.table_name_b in expr
