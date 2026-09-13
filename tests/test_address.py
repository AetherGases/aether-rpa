from datetime import datetime

from address import RegisterA, RegisterB, TableA, TableB
from address.extractor import extract_from_a, extract_from_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


def test_register_b_and_table_b_hold_address_fields() -> None:
    register = RegisterB(
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
    table = TableB(registers=[register])

    assert table.registers == [register]
    assert register.zip_code == "01310100"
    assert register.complement is None
    assert register.updated_at is None


def test_register_a_and_table_a_hold_address_fields() -> None:
    register = RegisterA(
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
    table = TableA(registers=[register])

    assert table.registers == [register]
    assert register.zip_code == "01310100"
    assert register.complement is None


def test_table_b_accepts_empty_registers() -> None:
    table = TableB(registers=[])

    assert table.registers == []


def test_table_a_accepts_empty_registers() -> None:
    table = TableA(registers=[])

    assert table.registers == []


COLUMNS = [
    "id",
    "zip_code",
    "state",
    "city",
    "neighborhood",
    "street",
    "number",
    "complement",
    "created_at",
    "updated_at",
]
SELECT_A = (
    "SELECT id, zip_code, state, city, neighborhood, street, number, "
    "complement, created_at, updated_at FROM addresses"
)
SELECT_B = (
    "SELECT id, zip_code, state, city, neighborhood, street, number, "
    "complement, created_at, updated_at FROM address"
)
ADDRESS_ROW = (
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


def test_extract_from_a_fills_register_a() -> None:
    connection, cursor = fake_connection(COLUMNS, [ADDRESS_ROW])

    table = extract_from_a(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert table == TableA(
        registers=[
            RegisterA(
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
        ]
    )


def test_extract_from_b_fills_register_b() -> None:
    connection, cursor = fake_connection(COLUMNS, [ADDRESS_ROW])

    table = extract_from_b(connection)

    cursor.execute.assert_called_once_with(SELECT_B)
    assert table == TableB(
        registers=[
            RegisterB(
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
        ]
    )


def test_extract_from_a_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS, [])

    table = extract_from_a(connection)

    assert table == TableA(registers=[])


def test_extract_from_b_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS, [])

    table = extract_from_b(connection)

    assert table == TableB(registers=[])
