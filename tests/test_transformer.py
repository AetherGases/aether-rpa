from dataclasses import dataclass
from datetime import datetime

from src.definition import (
    AddressA,
    AddressB,
    AddressTableA,
    AddressTableB,
    EmployeeB,
    EmployeeStatus,
    EmployeeTableB,
    EnterpriseA,
    EnterpriseB,
    EnterpriseTableA,
    EnterpriseTableB,
    PermissionGroupEmployeeA,
    PermissionGroupEmployeeB,
    PermissionGroupEmployeeTableA,
    PermissionGroupEmployeeTableB,
)
from src.transformer import transform, transform_to_a, transform_to_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


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


COMPANY_COLUMNS_A = [
    "id",
    "name",
    "trade_name",
    "cnpj",
    "created_at",
    "updated_at",
    "address_id",
]
COMPANY_COLUMNS_B = [
    "id",
    "name",
    "trade_name",
    "cnpj",
    "created_at",
    "updated_at",
    "id_address",
]
COMPANY_ROW = (1, "Aether Ltda", None, "12345678901234", CREATED_AT, None, 10)


def test_transform_to_b_companies_remaps_address_id() -> None:
    connection, _cursor = fake_connection(COMPANY_COLUMNS_A, [COMPANY_ROW])

    result = transform_to_b(connection, "companies")

    assert result == EnterpriseTableB(
        registers=[
            EnterpriseB(
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


def test_transform_to_a_companies_remaps_id_address() -> None:
    connection, _cursor = fake_connection(COMPANY_COLUMNS_B, [COMPANY_ROW])

    result = transform_to_a(connection, "companies")

    assert result == EnterpriseTableA(
        registers=[
            EnterpriseA(
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


def test_transform_to_b_employees_remaps_storage_file_and_sector_ids() -> None:
    connection, _cursor = fake_connection(EMPLOYEE_COLUMNS_A, [EMPLOYEE_ROW_A])

    result = transform_to_b(connection, "employees")

    assert result == EmployeeTableB(
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


def test_transform_to_b_empty_registers() -> None:
    connection, _cursor = fake_connection(COMPANY_COLUMNS_A, [])

    assert transform_to_b(connection, "companies") == EnterpriseTableB(registers=[])


def test_transform_to_a_empty_registers() -> None:
    connection, _cursor = fake_connection(COMPANY_COLUMNS_B, [])

    assert transform_to_a(connection, "companies") == EnterpriseTableA(registers=[])


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


def test_transform_to_b_addresses_copies_identical_fields() -> None:
    connection, _cursor = fake_connection(ADDRESS_COLUMNS, [ADDRESS_ROW])

    result = transform_to_b(connection, "addresses")

    assert result == AddressTableB(
        registers=[
            AddressB(
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


def test_transform_to_a_addresses_copies_identical_fields() -> None:
    connection, _cursor = fake_connection(ADDRESS_COLUMNS, [ADDRESS_ROW])

    result = transform_to_a(connection, "addresses")

    assert result == AddressTableA(
        registers=[
            AddressA(
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


PGE_COLUMNS_A = ["employee_id", "permission_group_id"]
PGE_COLUMNS_B = ["id_employee", "id_permission_group"]
PGE_ROW = (1, 2)


def test_transform_to_b_permission_group_employees_remaps_composite_ids() -> None:
    connection, _cursor = fake_connection(PGE_COLUMNS_A, [PGE_ROW])

    result = transform_to_b(connection, "permission_group_employees")

    assert result == PermissionGroupEmployeeTableB(
        registers=[PermissionGroupEmployeeB(id_employee=1, id_permission_group=2)]
    )


def test_transform_to_a_permission_group_employees_remaps_composite_ids() -> None:
    connection, _cursor = fake_connection(PGE_COLUMNS_B, [PGE_ROW])

    result = transform_to_a(connection, "permission_group_employees")

    assert result == PermissionGroupEmployeeTableA(
        registers=[PermissionGroupEmployeeA(employee_id=1, permission_group_id=2)]
    )
