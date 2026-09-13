from datetime import datetime

from plan_subscription import RegisterA, RegisterB, TableA, TableB
from plan_subscription.driver import drive_to_a, drive_to_b
from plan_subscription.extractor import extract_from_a, extract_from_b
from plan_subscription.transformer import transform_to_a, transform_to_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


def test_register_b_and_table_b_hold_plan_subscription_fields() -> None:
    register = RegisterB(
        id=1,
        is_active=True,
        installments=12,
        created_at=CREATED_AT,
        deactivated_at=None,
        id_plan=None,
        id_enterprise=None,
    )
    table = TableB(registers=[register])

    assert table.registers == [register]
    assert register.installments == 12
    assert register.deactivated_at is None
    assert register.id_plan is None


def test_register_a_and_table_a_hold_subscription_fields() -> None:
    register = RegisterA(
        id=1,
        is_active=True,
        installments=12,
        created_at=CREATED_AT,
        deactivated_at=None,
        plan_id=None,
        company_id=None,
    )
    table = TableA(registers=[register])

    assert table.registers == [register]
    assert register.plan_id is None
    assert register.company_id is None
    assert not hasattr(register, "id_enterprise")


def test_table_b_accepts_empty_registers() -> None:
    table = TableB(registers=[])

    assert table.registers == []


def test_table_a_accepts_empty_registers() -> None:
    table = TableA(registers=[])

    assert table.registers == []


COLUMNS_A = [
    "id",
    "is_active",
    "installments",
    "created_at",
    "deactivated_at",
    "plan_id",
    "company_id",
]
COLUMNS_B = [
    "id",
    "is_active",
    "installments",
    "created_at",
    "deactivated_at",
    "id_plan",
    "id_enterprise",
]
SELECT_A = (
    "SELECT id, is_active, installments, created_at, deactivated_at, plan_id, "
    "company_id FROM subscriptions"
)
SELECT_B = (
    "SELECT id, is_active, installments, created_at, deactivated_at, id_plan, "
    "id_enterprise FROM plan_subscription"
)
ROW_A = (1, True, 12, CREATED_AT, None, 7, 8)
ROW_B = (1, True, 12, CREATED_AT, None, 7, 8)


def test_extract_from_a_fills_register_a() -> None:
    connection, cursor = fake_connection(COLUMNS_A, [ROW_A])

    table = extract_from_a(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert table == TableA(
        registers=[
            RegisterA(
                id=1,
                is_active=True,
                installments=12,
                created_at=CREATED_AT,
                deactivated_at=None,
                plan_id=7,
                company_id=8,
            )
        ]
    )


def test_extract_from_b_fills_register_b() -> None:
    connection, cursor = fake_connection(COLUMNS_B, [ROW_B])

    table = extract_from_b(connection)

    cursor.execute.assert_called_once_with(SELECT_B)
    assert table == TableB(
        registers=[
            RegisterB(
                id=1,
                is_active=True,
                installments=12,
                created_at=CREATED_AT,
                deactivated_at=None,
                id_plan=7,
                id_enterprise=8,
            )
        ]
    )


def test_extract_from_a_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_A, [])

    assert extract_from_a(connection) == TableA(registers=[])


def test_extract_from_b_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_B, [])

    assert extract_from_b(connection) == TableB(registers=[])


def test_transform_to_b_remaps_plan_and_company_ids() -> None:
    connection, _cursor = fake_connection(COLUMNS_A, [ROW_A])

    result = transform_to_b(connection)

    assert result == TableB(
        registers=[
            RegisterB(
                id=1,
                is_active=True,
                installments=12,
                created_at=CREATED_AT,
                deactivated_at=None,
                id_plan=7,
                id_enterprise=8,
            )
        ]
    )


def test_transform_to_a_remaps_plan_and_enterprise_ids() -> None:
    connection, _cursor = fake_connection(COLUMNS_B, [ROW_B])

    result = transform_to_a(connection)

    assert result == TableA(
        registers=[
            RegisterA(
                id=1,
                is_active=True,
                installments=12,
                created_at=CREATED_AT,
                deactivated_at=None,
                plan_id=7,
                company_id=8,
            )
        ]
    )


def test_transform_to_b_empty_registers() -> None:
    connection, _cursor = fake_connection(COLUMNS_A, [])

    assert transform_to_b(connection) == TableB(registers=[])


def test_transform_to_a_empty_registers() -> None:
    connection, _cursor = fake_connection(COLUMNS_B, [])

    assert transform_to_a(connection) == TableA(registers=[])


def test_drive_to_b_insert() -> None:
    source_a, _ = fake_connection(COLUMNS_A, [ROW_A])
    dest_b, dest_cursor = fake_connection(COLUMNS_B, [])

    drive_to_b(source_a, dest_b, "insert")

    dest_cursor.executemany.assert_called_once_with(
        "INSERT INTO plan_subscription (id, is_active, installments, created_at, deactivated_at, id_plan, id_enterprise) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        [(1, True, 12, CREATED_AT, None, 7, 8)],
    )


def test_drive_to_a_update() -> None:
    dest_a, dest_cursor = fake_connection(COLUMNS_A, [])
    source_b, _ = fake_connection(COLUMNS_B, [ROW_B])

    drive_to_a(dest_a, source_b, "update")

    dest_cursor.executemany.assert_called_once_with(
        "UPDATE subscriptions SET is_active = %s, installments = %s, created_at = %s, deactivated_at = %s, plan_id = %s, company_id = %s WHERE id = %s",
        [(True, 12, CREATED_AT, None, 7, 8, 1)],
    )


def test_drive_to_b_empty_source_does_not_execute() -> None:
    source_a, _ = fake_connection(COLUMNS_A, [])
    dest_b, dest_cursor = fake_connection(COLUMNS_B, [])

    drive_to_b(source_a, dest_b, "insert")

    dest_cursor.executemany.assert_not_called()
