from dataclasses import dataclass
from datetime import datetime

import pytest

from src.definition import (
    TABLES,
    AddressA,
    AddressB,
    AddressTableA,
    AddressTableB,
    EmployeeA,
    EmployeeB,
    EmployeeStatus,
    EmployeeTableA,
    EmployeeTableB,
)
from src.extractor import extract, extract_from_a, extract_from_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


@dataclass
class _Register:
    id: int
    name: str


@dataclass
class _Table:
    registers: list[_Register]


QUERY = "SELECT id, name FROM items"

ADDRESS_COLUMNS = [
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
ADDRESS_A = AddressA(
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
ADDRESS_B = AddressB(
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

EMPLOYEE_COLUMNS_A = [
    "id",
    "cpf",
    "name",
    "email",
    "phone",
    "password_hash",
    "employee_status",
    "created_at",
    "updated_at",
    "storage_file_id",
    "sector_id",
]
EMPLOYEE_COLUMNS_B = [
    "id",
    "cpf",
    "name",
    "email",
    "phone",
    "password_hash",
    "employee_status",
    "created_at",
    "updated_at",
    "id_storage_file",
    "id_department",
]
EMPLOYEE_ROW_A = (
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
EMPLOYEE_ROW_B = (
    1,
    "12345678901",
    "Ana Silva",
    "ana@example.com",
    "11999999999",
    "hash",
    "IN_VACATION",
    CREATED_AT,
    None,
    5,
    6,
)


def test_extract_executes_query_and_fills_table() -> None:
    connection, cursor = fake_connection(["id", "name"], [(1, "alpha")])

    table = extract(connection, QUERY, _Register, _Table)

    cursor.execute.assert_called_once_with(QUERY)
    assert table == _Table(registers=[_Register(id=1, name="alpha")])


def test_extract_empty_rows_returns_empty_table() -> None:
    connection, _cursor = fake_connection(["id", "name"], [])

    table = extract(connection, QUERY, _Register, _Table)

    assert table == _Table(registers=[])


def test_extract_from_a_fills_address_register() -> None:
    connection, cursor = fake_connection(ADDRESS_COLUMNS, [ADDRESS_ROW])

    table = extract_from_a(connection, "addresses")

    cursor.execute.assert_called_once_with(TABLES["addresses"].select_a)
    assert table == AddressTableA(registers=[ADDRESS_A])


def test_extract_from_b_fills_address_register() -> None:
    connection, cursor = fake_connection(ADDRESS_COLUMNS, [ADDRESS_ROW])

    table = extract_from_b(connection, "addresses")

    cursor.execute.assert_called_once_with(TABLES["addresses"].select_b)
    assert table == AddressTableB(registers=[ADDRESS_B])


def test_extract_from_a_fills_employee_with_active_status() -> None:
    connection, cursor = fake_connection(EMPLOYEE_COLUMNS_A, [EMPLOYEE_ROW_A])

    table = extract_from_a(connection, "employees")

    cursor.execute.assert_called_once_with(TABLES["employees"].select_a)
    assert table == EmployeeTableA(
        registers=[
            EmployeeA(
                id=1,
                cpf="12345678901",
                name="Ana Silva",
                email="ana@example.com",
                phone="11999999999",
                password_hash="hash",
                employee_status=EmployeeStatus.ACTIVE,
                created_at=CREATED_AT,
                updated_at=None,
                storage_file_id=5,
                sector_id=6,
            )
        ]
    )


def test_extract_from_b_fills_employee_with_in_vacation_status() -> None:
    connection, cursor = fake_connection(EMPLOYEE_COLUMNS_B, [EMPLOYEE_ROW_B])

    table = extract_from_b(connection, "employees")

    cursor.execute.assert_called_once_with(TABLES["employees"].select_b)
    assert table == EmployeeTableB(
        registers=[
            EmployeeB(
                id=1,
                cpf="12345678901",
                name="Ana Silva",
                email="ana@example.com",
                phone="11999999999",
                password_hash="hash",
                employee_status=EmployeeStatus.IN_VACATION,
                created_at=CREATED_AT,
                updated_at=None,
                id_storage_file=5,
                id_department=6,
            )
        ]
    )


def test_extract_from_a_empty_rows() -> None:
    connection, _cursor = fake_connection(ADDRESS_COLUMNS, [])

    table = extract_from_a(connection, "addresses")

    assert table == AddressTableA(registers=[])


@pytest.mark.parametrize("table_key", list(TABLES))
def test_extract_from_a_executes_select_a_for_every_table(table_key: str) -> None:
    spec = TABLES[table_key]
    connection, cursor = fake_connection(["id"], [])

    table = extract_from_a(connection, table_key)

    cursor.execute.assert_called_once_with(spec.select_a)
    assert table == spec.table_a(registers=[])
