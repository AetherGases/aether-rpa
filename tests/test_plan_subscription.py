from datetime import datetime

from plan_subscription import RegisterA, RegisterB, TableA, TableB
from plan_subscription.extractor import extract_from_a, extract_from_b
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
ROW = (1, True, 12, CREATED_AT, None, 7, 8)


def test_extract_from_a_fills_register_a() -> None:
    connection, cursor = fake_connection(COLUMNS_A, [ROW])

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
    connection, cursor = fake_connection(COLUMNS_B, [ROW])

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


from plan_subscription.transformer import transform_to_a, transform_to_b


def test_transform_to_b_remaps_plan_and_company_ids() -> None:
    table = TableA(
        registers=[
            RegisterA(
                id=1,
                is_active=True,
                installments=12,
                created_at=CREATED_AT,
                deactivated_at=None,
                plan_id=9,
                company_id=3,
            )
        ]
    )
    result = transform_to_b(table)
    assert result == TableB(
        registers=[
            RegisterB(
                id=1,
                is_active=True,
                installments=12,
                created_at=CREATED_AT,
                deactivated_at=None,
                id_plan=9,
                id_enterprise=3,
            )
        ]
    )


def test_transform_to_a_remaps_plan_and_enterprise_ids() -> None:
    table = TableB(
        registers=[
            RegisterB(
                id=1,
                is_active=True,
                installments=12,
                created_at=CREATED_AT,
                deactivated_at=None,
                id_plan=9,
                id_enterprise=3,
            )
        ]
    )
    result = transform_to_a(table)
    assert result == TableA(
        registers=[
            RegisterA(
                id=1,
                is_active=True,
                installments=12,
                created_at=CREATED_AT,
                deactivated_at=None,
                plan_id=9,
                company_id=3,
            )
        ]
    )


def test_transform_to_b_empty_registers() -> None:
    assert transform_to_b(TableA(registers=[])) == TableB(registers=[])


def test_transform_to_a_empty_registers() -> None:
    assert transform_to_a(TableB(registers=[])) == TableA(registers=[])
