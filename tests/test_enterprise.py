from datetime import datetime

from enterprise import RegisterA, RegisterB, TableA, TableB
from enterprise.extractor import extract_from_a, extract_from_b
from enterprise.transformer import transform_to_a, transform_to_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


def test_register_b_and_table_b_hold_enterprise_fields() -> None:
    register = RegisterB(
        id=1,
        name="Aether Ltda",
        trade_name=None,
        cnpj="12345678901234",
        created_at=CREATED_AT,
        updated_at=None,
        id_address=None,
    )
    table = TableB(registers=[register])

    assert table.registers == [register]
    assert register.name == "Aether Ltda"
    assert register.trade_name is None
    assert register.id_address is None


def test_register_a_and_table_a_hold_company_fields() -> None:
    register = RegisterA(
        id=1,
        name="Aether Ltda",
        trade_name=None,
        cnpj="12345678901234",
        created_at=CREATED_AT,
        updated_at=None,
        address_id=None,
    )
    table = TableA(registers=[register])

    assert table.registers == [register]
    assert register.address_id is None
    assert not hasattr(register, "id_address")


def test_table_b_accepts_empty_registers() -> None:
    table = TableB(registers=[])

    assert table.registers == []


def test_table_a_accepts_empty_registers() -> None:
    table = TableA(registers=[])

    assert table.registers == []


COLUMNS_A = ["id", "name", "trade_name", "cnpj", "created_at", "updated_at", "address_id"]
COLUMNS_B = ["id", "name", "trade_name", "cnpj", "created_at", "updated_at", "id_address"]
SELECT_A = (
    "SELECT id, name, trade_name, cnpj, created_at, updated_at, address_id FROM companies"
)
SELECT_B = (
    "SELECT id, name, trade_name, cnpj, created_at, updated_at, id_address FROM enterprise"
)
ROW_A = (1, "Aether Ltda", None, "12345678901234", CREATED_AT, None, 10)
ROW_B = (1, "Aether Ltda", None, "12345678901234", CREATED_AT, None, 10)


def test_extract_from_a_fills_register_a() -> None:
    connection, cursor = fake_connection(COLUMNS_A, [ROW_A])

    table = extract_from_a(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert table == TableA(
        registers=[
            RegisterA(
                id=1,
                name="Aether Ltda",
                trade_name=None,
                cnpj="12345678901234",
                created_at=CREATED_AT,
                updated_at=None,
                address_id=10,
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
                name="Aether Ltda",
                trade_name=None,
                cnpj="12345678901234",
                created_at=CREATED_AT,
                updated_at=None,
                id_address=10,
            )
        ]
    )


def test_extract_from_a_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_A, [])

    assert extract_from_a(connection) == TableA(registers=[])


def test_extract_from_b_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_B, [])

    assert extract_from_b(connection) == TableB(registers=[])


def test_transform_to_b_remaps_address_id() -> None:
    table = TableA(
        registers=[
            RegisterA(
                id=1,
                name="Aether Ltda",
                trade_name=None,
                cnpj="12345678901234",
                created_at=CREATED_AT,
                updated_at=None,
                address_id=10,
            )
        ]
    )

    result = transform_to_b(table)

    assert result == TableB(
        registers=[
            RegisterB(
                id=1,
                name="Aether Ltda",
                trade_name=None,
                cnpj="12345678901234",
                created_at=CREATED_AT,
                updated_at=None,
                id_address=10,
            )
        ]
    )


def test_transform_to_a_remaps_id_address() -> None:
    table = TableB(
        registers=[
            RegisterB(
                id=1,
                name="Aether Ltda",
                trade_name=None,
                cnpj="12345678901234",
                created_at=CREATED_AT,
                updated_at=None,
                id_address=10,
            )
        ]
    )

    result = transform_to_a(table)

    assert result == TableA(
        registers=[
            RegisterA(
                id=1,
                name="Aether Ltda",
                trade_name=None,
                cnpj="12345678901234",
                created_at=CREATED_AT,
                updated_at=None,
                address_id=10,
            )
        ]
    )


def test_transform_to_b_empty_registers() -> None:
    assert transform_to_b(TableA(registers=[])) == TableB(registers=[])


def test_transform_to_a_empty_registers() -> None:
    assert transform_to_a(TableB(registers=[])) == TableA(registers=[])
