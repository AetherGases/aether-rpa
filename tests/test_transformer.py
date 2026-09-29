from dataclasses import dataclass
from datetime import datetime

import pytest

from src.definition import (
    AddressA,
    AddressB,
    AddressTableA,
    AddressTableB,
    EmployeeA,
    EmployeeB,
    StatusEmployee,
    EmployeeTableA,
    EmployeeTableB,
    EnterpriseA,
    EnterpriseB,
    EnterpriseTableA,
    EnterpriseTableB,
    PermissionGroupA,
    PermissionGroupB,
    PermissionGroupTableA,
    PermissionGroupTableB,
    PlanSubscriptionA,
    PlanSubscriptionB,
    PlanSubscriptionTableA,
    PlanSubscriptionTableB,
    TransformError,
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

    result = transform(
        table, _RegisterB, _TableB, _FIELD_MAP, "companies", to_b=True
    )

    assert result == _TableB(registers=[_RegisterB(id=1, name="alpha", id_address=10)])


def test_transform_empty_registers_returns_empty_table() -> None:
    result = transform(
        _TableA(registers=[]), _RegisterB, _TableB, _FIELD_MAP, "companies", to_b=True
    )

    assert result == _TableB(registers=[])


def test_transform_applies_inverse_field_map() -> None:
    inverse = {target: source for source, target in _FIELD_MAP.items()}
    table = _TableB(registers=[_RegisterB(id=1, name="alpha", id_address=10)])

    result = transform(
        table, _RegisterA, _TableA, inverse, "companies", to_b=False
    )

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
    "status",
    "created_at",
    "updated_at",
    "storage_file_id",
    "sector_id",
    "permission_group_id",
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
    "id_permission_group",
]
EMPLOYEE_ROW_A = (
    1,
    "12345678901",
    "Ana Silva",
    "ana@example.com",
    "11999999999",
    "hash",
    "active",
    CREATED_AT,
    None,
    5,
    6,
    2,
)


def test_transform_to_b_employees_remaps_ids_and_status() -> None:
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
                employee_status=StatusEmployee.ACTIVE,
                created_at=CREATED_AT,
                updated_at=None,
                id_storage_file=5,
                id_department=6,
                id_permission_group=2,
            )
        ]
    )


def test_transform_to_b_empty_registers() -> None:
    connection, _cursor = fake_connection(COMPANY_COLUMNS_A, [])

    assert transform_to_b(connection, "companies") == EnterpriseTableB(registers=[])


def test_transform_to_a_empty_registers() -> None:
    connection, _cursor = fake_connection(COMPANY_COLUMNS_B, [])

    assert transform_to_a(connection, "companies") == EnterpriseTableA(registers=[])


ADDRESS_COLUMNS_A = [
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
ADDRESS_ROW_A = (
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
ADDRESS_ROW_B = (
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


def test_transform_to_b_addresses_converts_number_str_to_int() -> None:
    connection, _cursor = fake_connection(ADDRESS_COLUMNS_A, [ADDRESS_ROW_A])

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


def test_transform_to_a_addresses_converts_number_int_to_str() -> None:
    connection, _cursor = fake_connection(ADDRESS_COLUMNS_A, [ADDRESS_ROW_B])

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
                number="1000",
                complement=None,
                created_at=CREATED_AT,
                updated_at=None,
            )
        ]
    )


def test_transform_to_b_addresses_raises_for_non_numeric_number() -> None:
    bad_row = (*ADDRESS_ROW_A[:6], "abc", *ADDRESS_ROW_A[7:])
    connection, _cursor = fake_connection(ADDRESS_COLUMNS_A, [bad_row])

    with pytest.raises(TransformError, match="not numeric"):
        transform_to_b(connection, "addresses")


PERMISSION_GROUP_COLUMNS_A = [
    "id",
    "name",
    "created_at",
    "company_id",
]
PERMISSION_GROUP_COLUMNS_B = [
    "id",
    "description",
    "created_at",
    "id_enterprise",
]
PERMISSION_GROUP_ROW = (1, "admin", CREATED_AT, 3)


def test_transform_to_b_permission_groups_remaps_name_and_company() -> None:
    connection, _cursor = fake_connection(
        PERMISSION_GROUP_COLUMNS_A, [PERMISSION_GROUP_ROW]
    )

    result = transform_to_b(connection, "permission_groups")

    assert result == PermissionGroupTableB(
        registers=[
            PermissionGroupB(
                id=1,
                description="admin",
                created_at=CREATED_AT,
                id_enterprise=3,
            )
        ]
    )


def test_transform_to_a_permission_groups_remaps_description_and_enterprise() -> None:
    connection, _cursor = fake_connection(
        PERMISSION_GROUP_COLUMNS_B, [PERMISSION_GROUP_ROW]
    )

    result = transform_to_a(connection, "permission_groups")

    assert result == PermissionGroupTableA(
        registers=[
            PermissionGroupA(
                id=1,
                name="admin",
                created_at=CREATED_AT,
                company_id=3,
            )
        ]
    )


SUBSCRIPTION_COLUMNS_A = [
    "id",
    "is_active",
    "installments",
    "created_at",
    "deactivated_at",
    "plan_id",
    "company_id",
]
SUBSCRIPTION_COLUMNS_B = [
    "id",
    "is_active",
    "installments",
    "created_at",
    "deactivated_at",
    "id_plan",
    "id_enterprise",
]
SUBSCRIPTION_BASE = (1, True, CREATED_AT, None, 1, 1)


@pytest.mark.parametrize(
    ("installments_a", "installments_b"),
    [
        (False, 0),
        (True, 1),
    ],
)
def test_transform_to_b_subscriptions_converts_bool_to_int(
    installments_a: bool, installments_b: int
) -> None:
    row = (1, True, installments_a, CREATED_AT, None, 1, 1)
    connection, _cursor = fake_connection(SUBSCRIPTION_COLUMNS_A, [row])

    result = transform_to_b(connection, "subscriptions")

    assert result.registers[0].installments == installments_b


@pytest.mark.parametrize(
    ("installments_b", "installments_a"),
    [
        (0, False),
        (1, True),
        (12, True),
    ],
)
def test_transform_to_a_subscriptions_converts_int_to_bool(
    installments_b: int, installments_a: bool
) -> None:
    row = (1, True, installments_b, CREATED_AT, None, 1, 1)
    connection, _cursor = fake_connection(SUBSCRIPTION_COLUMNS_B, [row])

    result = transform_to_a(connection, "subscriptions")

    assert result.registers[0].installments is installments_a


def test_transform_to_b_subscriptions_raises_for_null_installments() -> None:
    row = (1, True, None, CREATED_AT, None, 1, 1)
    connection, _cursor = fake_connection(SUBSCRIPTION_COLUMNS_A, [row])

    with pytest.raises(TransformError, match="installments cannot be null"):
        transform_to_b(connection, "subscriptions")


@pytest.mark.parametrize(
    "status",
    ["active", "on vacation", "on leave", "dismissed"],
)
def test_transform_to_b_employees_preserves_status(status: str) -> None:
    row = (*EMPLOYEE_ROW_A[:6], status, *EMPLOYEE_ROW_A[7:])
    connection, _cursor = fake_connection(EMPLOYEE_COLUMNS_A, [row])

    result = transform_to_b(connection, "employees")

    assert result.registers[0].employee_status == StatusEmployee(status)


@pytest.mark.parametrize(
    "status",
    ["active", "on vacation", "on leave", "dismissed"],
)
def test_transform_to_a_employees_preserves_status(status: str) -> None:
    row = (*EMPLOYEE_ROW_A[:6], status, *EMPLOYEE_ROW_A[7:11], 2)
    connection, _cursor = fake_connection(EMPLOYEE_COLUMNS_B, [row])

    result = transform_to_a(connection, "employees")

    assert result.registers[0].status == StatusEmployee(status)


def test_dismissed_round_trip_preserves_status() -> None:
    row_a = (*EMPLOYEE_ROW_A[:6], "dismissed", *EMPLOYEE_ROW_A[7:])
    connection_a, _ = fake_connection(EMPLOYEE_COLUMNS_A, [row_a])
    to_b = transform_to_b(connection_a, "employees")
    assert to_b.registers[0].employee_status == StatusEmployee.DISMISSED

    row_b = (
        1,
        "12345678901",
        "Ana Silva",
        "ana@example.com",
        "11999999999",
        "hash",
        "dismissed",
        CREATED_AT,
        None,
        5,
        6,
        2,
    )
    connection_b, _ = fake_connection(EMPLOYEE_COLUMNS_B, [row_b])
    to_a = transform_to_a(connection_b, "employees")
    assert to_a.registers[0].status == StatusEmployee.DISMISSED


def test_installments_round_trip_loss_above_one() -> None:
    row_b = (1, True, 12, CREATED_AT, None, 1, 1)
    connection_b, _ = fake_connection(SUBSCRIPTION_COLUMNS_B, [row_b])
    to_a = transform_to_a(connection_b, "subscriptions")
    assert to_a.registers[0].installments is True

    row_a = (1, True, True, CREATED_AT, None, 1, 1)
    connection_a, _ = fake_connection(SUBSCRIPTION_COLUMNS_A, [row_a])
    to_b = transform_to_b(connection_a, "subscriptions")
    assert to_b.registers[0].installments == 1


def test_transform_to_a_subscriptions_raises_for_null_installments() -> None:
    row = (1, True, None, CREATED_AT, None, 1, 1)
    connection, _cursor = fake_connection(SUBSCRIPTION_COLUMNS_B, [row])

    with pytest.raises(TransformError, match="installments cannot be null"):
        transform_to_a(connection, "subscriptions")


def test_transform_to_a_addresses_raises_for_null_number() -> None:
    row = (*ADDRESS_ROW_B[:6], None, *ADDRESS_ROW_B[7:])
    connection, _cursor = fake_connection(ADDRESS_COLUMNS_A, [row])

    with pytest.raises(TransformError, match="address number cannot be null"):
        transform_to_a(connection, "addresses")


def test_transform_to_b_addresses_raises_for_null_number() -> None:
    row = (*ADDRESS_ROW_A[:6], None, *ADDRESS_ROW_A[7:])
    connection, _cursor = fake_connection(ADDRESS_COLUMNS_A, [row])

    with pytest.raises(TransformError, match="address number cannot be null"):
        transform_to_b(connection, "addresses")

