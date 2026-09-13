from datetime import datetime

from unit import RegisterA, RegisterB, TableA, TableB
from tests.fake_db import fake_connection
from unit.driver import drive_to_a, drive_to_b
from unit.extractor import extract_from_a, extract_from_b
from unit.transformer import transform_to_a, transform_to_b

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


def test_register_b_and_table_b_hold_unit_fields() -> None:
    register = RegisterB(
        id=1,
        cnae=None,
        cnpj="12345678901234",
        is_active=True,
        created_at=CREATED_AT,
        updated_at=None,
        id_enterprise=None,
        id_address=None,
    )
    table = TableB(registers=[register])

    assert table.registers == [register]
    assert register.is_active is True
    assert register.cnae is None
    assert register.id_enterprise is None


def test_register_a_and_table_a_hold_unit_fields() -> None:
    register = RegisterA(
        id=1,
        cnae=None,
        cnpj="12345678901234",
        is_active=True,
        created_at=CREATED_AT,
        updated_at=None,
        company_id=None,
        address_id=None,
    )
    table = TableA(registers=[register])

    assert table.registers == [register]
    assert register.company_id is None
    assert register.address_id is None
    assert not hasattr(register, "id_enterprise")


def test_table_b_accepts_empty_registers() -> None:
    table = TableB(registers=[])

    assert table.registers == []


def test_table_a_accepts_empty_registers() -> None:
    table = TableA(registers=[])

    assert table.registers == []


COLUMNS_A = [
    "id",
    "cnae",
    "cnpj",
    "is_active",
    "created_at",
    "updated_at",
    "company_id",
    "address_id",
]
COLUMNS_B = [
    "id",
    "cnae",
    "cnpj",
    "is_active",
    "created_at",
    "updated_at",
    "id_enterprise",
    "id_address",
]
SELECT_A = (
    "SELECT id, cnae, cnpj, is_active, created_at, updated_at, company_id, "
    "address_id FROM units"
)
SELECT_B = (
    "SELECT id, cnae, cnpj, is_active, created_at, updated_at, id_enterprise, "
    "id_address FROM unit"
)
ROW = (1, None, "12345678901234", True, CREATED_AT, None, 2, 3)
ROW_REMAP = (1, None, "12345678901234", True, CREATED_AT, None, 3, 10)


def test_extract_from_a_fills_register_a() -> None:
    connection, cursor = fake_connection(COLUMNS_A, [ROW])

    table = extract_from_a(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert table == TableA(
        registers=[
            RegisterA(
                id=1,
                cnae=None,
                cnpj="12345678901234",
                is_active=True,
                created_at=CREATED_AT,
                updated_at=None,
                company_id=2,
                address_id=3,
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
                cnae=None,
                cnpj="12345678901234",
                is_active=True,
                created_at=CREATED_AT,
                updated_at=None,
                id_enterprise=2,
                id_address=3,
            )
        ]
    )


def test_extract_from_a_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_A, [])

    assert extract_from_a(connection) == TableA(registers=[])


def test_extract_from_b_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_B, [])

    assert extract_from_b(connection) == TableB(registers=[])


def test_transform_to_b_remaps_company_and_address_ids() -> None:
    connection, _cursor = fake_connection(COLUMNS_A, [ROW_REMAP])

    result = transform_to_b(connection)

    assert result == TableB(
        registers=[
            RegisterB(
                id=1,
                cnae=None,
                cnpj="12345678901234",
                is_active=True,
                created_at=CREATED_AT,
                updated_at=None,
                id_enterprise=3,
                id_address=10,
            )
        ]
    )


def test_transform_to_a_remaps_enterprise_and_address_ids() -> None:
    connection, _cursor = fake_connection(COLUMNS_B, [ROW_REMAP])

    result = transform_to_a(connection)

    assert result == TableA(
        registers=[
            RegisterA(
                id=1,
                cnae=None,
                cnpj="12345678901234",
                is_active=True,
                created_at=CREATED_AT,
                updated_at=None,
                company_id=3,
                address_id=10,
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
    connection_a, _cursor_a = fake_connection(COLUMNS_A, [ROW])
    connection_b, cursor_b = fake_connection(COLUMNS_B, [])

    drive_to_b(connection_a, connection_b, "insert")

    cursor_b.executemany.assert_called_once_with(
        "INSERT INTO unit (id, cnae, cnpj, is_active, created_at, updated_at, "
        "id_enterprise, id_address) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        [(1, None, "12345678901234", True, CREATED_AT, None, 2, 3)],
    )


def test_drive_to_a_update() -> None:
    connection_a, cursor_a = fake_connection(COLUMNS_A, [])
    connection_b, _cursor_b = fake_connection(COLUMNS_B, [ROW])

    drive_to_a(connection_a, connection_b, "update")

    cursor_a.executemany.assert_called_once_with(
        "UPDATE units SET cnae = %s, cnpj = %s, is_active = %s, created_at = %s, "
        "updated_at = %s, company_id = %s, address_id = %s WHERE id = %s",
        [(None, "12345678901234", True, CREATED_AT, None, 2, 3, 1)],
    )


def test_drive_to_b_empty_no_op() -> None:
    connection_a, _cursor_a = fake_connection(COLUMNS_A, [])
    connection_b, cursor_b = fake_connection(COLUMNS_B, [])

    drive_to_b(connection_a, connection_b, "insert")

    cursor_b.executemany.assert_not_called()
    connection_b.cursor.assert_not_called()
