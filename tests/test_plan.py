from datetime import datetime
from decimal import Decimal

from plan import RegisterA, RegisterB, TableA, TableB
from plan.extractor import extract_from_a, extract_from_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


def test_register_b_and_table_b_hold_plan_fields() -> None:
    register = RegisterB(
        id=1,
        name="Pro",
        description=None,
        price=Decimal("99.90"),
        duration_days=30,
        is_active=True,
        created_at=CREATED_AT,
        updated_at=None,
    )
    table = TableB(registers=[register])

    assert table.registers == [register]
    assert register.price == Decimal("99.90")
    assert register.description is None
    assert register.duration_days == 30


def test_register_a_and_table_a_hold_plan_fields() -> None:
    register = RegisterA(
        id=1,
        name="Pro",
        description=None,
        price=Decimal("99.90"),
        duration_days=30,
        is_active=True,
        created_at=CREATED_AT,
        updated_at=None,
    )
    table = TableA(registers=[register])

    assert table.registers == [register]
    assert register.price == Decimal("99.90")


def test_table_b_accepts_empty_registers() -> None:
    table = TableB(registers=[])

    assert table.registers == []


def test_table_a_accepts_empty_registers() -> None:
    table = TableA(registers=[])

    assert table.registers == []


COLUMNS = [
    "id",
    "name",
    "description",
    "price",
    "duration_days",
    "is_active",
    "created_at",
    "updated_at",
]
SELECT_A = (
    "SELECT id, name, description, price, duration_days, is_active, "
    "created_at, updated_at FROM plans"
)
SELECT_B = (
    "SELECT id, name, description, price, duration_days, is_active, "
    "created_at, updated_at FROM plan"
)
ROW = (1, "Pro", None, Decimal("99.90"), 30, True, CREATED_AT, None)


def test_extract_from_a_fills_register_a() -> None:
    connection, cursor = fake_connection(COLUMNS, [ROW])

    table = extract_from_a(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert table == TableA(
        registers=[
            RegisterA(
                id=1,
                name="Pro",
                description=None,
                price=Decimal("99.90"),
                duration_days=30,
                is_active=True,
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
                name="Pro",
                description=None,
                price=Decimal("99.90"),
                duration_days=30,
                is_active=True,
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
