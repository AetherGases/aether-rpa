from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class EmployeeStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    IN_VACATION = "IN_VACATION"


@dataclass
class AddressA:
    id: int
    zip_code: str | None
    state: str
    city: str
    neighborhood: str
    street: str
    number: int
    complement: str | None
    created_at: datetime
    updated_at: datetime | None


@dataclass
class AddressTableA:
    registers: list[AddressA]


@dataclass
class AddressB:
    id: int
    zip_code: str | None
    state: str
    city: str
    neighborhood: str
    street: str
    number: int
    complement: str | None
    created_at: datetime
    updated_at: datetime | None


@dataclass
class AddressTableB:
    registers: list[AddressB]


@dataclass
class EnterpriseA:
    id: int
    name: str
    trade_name: str | None
    cnpj: str
    created_at: datetime
    updated_at: datetime | None
    address_id: int | None


@dataclass
class EnterpriseTableA:
    registers: list[EnterpriseA]


@dataclass
class EnterpriseB:
    id: int
    name: str
    trade_name: str | None
    cnpj: str
    created_at: datetime
    updated_at: datetime | None
    id_address: int | None


@dataclass
class EnterpriseTableB:
    registers: list[EnterpriseB]


@dataclass
class UnitA:
    id: int
    cnae: str | None
    cnpj: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
    company_id: int | None
    address_id: int | None


@dataclass
class UnitTableA:
    registers: list[UnitA]


@dataclass
class UnitB:
    id: int
    cnae: str | None
    cnpj: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
    id_enterprise: int | None
    id_address: int | None


@dataclass
class UnitTableB:
    registers: list[UnitB]


@dataclass
class DepartmentA:
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    unit_id: int | None


@dataclass
class DepartmentTableA:
    registers: list[DepartmentA]


@dataclass
class DepartmentB:
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    id_unit: int | None


@dataclass
class DepartmentTableB:
    registers: list[DepartmentB]


@dataclass
class StorageFileA:
    id: int
    name: str
    path: str
    created_at: datetime
    updated_at: datetime | None


@dataclass
class StorageFileTableA:
    registers: list[StorageFileA]


@dataclass
class StorageFileB:
    id: int
    name: str
    path: str
    created_at: datetime
    updated_at: datetime | None


@dataclass
class StorageFileTableB:
    registers: list[StorageFileB]


@dataclass
class PermissionGroupA:
    id: int
    description: str
    created_at: datetime


@dataclass
class PermissionGroupTableA:
    registers: list[PermissionGroupA]


@dataclass
class PermissionGroupB:
    id: int
    description: str
    created_at: datetime


@dataclass
class PermissionGroupTableB:
    registers: list[PermissionGroupB]


@dataclass
class PermissionA:
    id: int
    name: str
    description: str | None
    url: str
    created_at: datetime
    updated_at: datetime | None


@dataclass
class PermissionTableA:
    registers: list[PermissionA]


@dataclass
class PermissionB:
    id: int
    name: str
    description: str | None
    url: str
    created_at: datetime
    updated_at: datetime | None


@dataclass
class PermissionTableB:
    registers: list[PermissionB]


@dataclass
class PermissionGroupPermissionA:
    id: int
    created_at: datetime
    updated_at: datetime | None
    permission_id: int | None
    permission_group_id: int | None


@dataclass
class PermissionGroupPermissionTableA:
    registers: list[PermissionGroupPermissionA]


@dataclass
class PermissionGroupPermissionB:
    id: int
    created_at: datetime
    updated_at: datetime | None
    id_permission: int | None
    id_permission_group: int | None


@dataclass
class PermissionGroupPermissionTableB:
    registers: list[PermissionGroupPermissionB]


@dataclass
class EmployeeA:
    id: int
    cpf: str
    name: str
    email: str
    phone: str
    password_hash: str
    employee_status: EmployeeStatus
    created_at: datetime
    updated_at: datetime | None
    storage_file_id: int | None
    sector_id: int | None


@dataclass
class EmployeeTableA:
    registers: list[EmployeeA]


@dataclass
class EmployeeB:
    id: int
    cpf: str
    name: str
    email: str
    phone: str
    password_hash: str
    employee_status: EmployeeStatus
    created_at: datetime
    updated_at: datetime | None
    id_storage_file: int | None
    id_department: int | None


@dataclass
class EmployeeTableB:
    registers: list[EmployeeB]


@dataclass
class PermissionGroupEmployeeA:
    employee_id: int
    permission_group_id: int


@dataclass
class PermissionGroupEmployeeTableA:
    registers: list[PermissionGroupEmployeeA]


@dataclass
class PermissionGroupEmployeeB:
    id_employee: int
    id_permission_group: int


@dataclass
class PermissionGroupEmployeeTableB:
    registers: list[PermissionGroupEmployeeB]


@dataclass
class PlanA:
    id: int
    name: str
    description: str | None
    price: Decimal
    duration_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


@dataclass
class PlanTableA:
    registers: list[PlanA]


@dataclass
class PlanB:
    id: int
    name: str
    description: str | None
    price: Decimal
    duration_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


@dataclass
class PlanTableB:
    registers: list[PlanB]


@dataclass
class PlanSubscriptionA:
    id: int
    is_active: bool
    installments: int
    created_at: datetime
    deactivated_at: datetime | None
    plan_id: int | None
    company_id: int | None


@dataclass
class PlanSubscriptionTableA:
    registers: list[PlanSubscriptionA]


@dataclass
class PlanSubscriptionB:
    id: int
    is_active: bool
    installments: int
    created_at: datetime
    deactivated_at: datetime | None
    id_plan: int | None
    id_enterprise: int | None


@dataclass
class PlanSubscriptionTableB:
    registers: list[PlanSubscriptionB]


@dataclass(frozen=True)
class TableSpec:
    register_a: type
    register_b: type
    table_a: type
    table_b: type
    select_a: str
    select_b: str
    field_map: dict[str, str]
    table_name_a: str
    table_name_b: str
    pk_a: tuple[str, ...]
    pk_b: tuple[str, ...]
    enum_fields: tuple[str, ...] = ()


TABLE_ORDER = [
    "addresses",
    "storage_files",
    "permission_groups",
    "permissions",
    "plans",
    "companies",
    "units",
    "sectors",
    "permission_group_permissions",
    "employees",
    "permission_group_employees",
    "subscriptions",
]

TABLES = {
    "addresses": TableSpec(
        register_a=AddressA,
        register_b=AddressB,
        table_a=AddressTableA,
        table_b=AddressTableB,
        select_a=(
            "SELECT id, zip_code, state, city, neighborhood, street, number, "
            "complement, created_at, updated_at FROM addresses"
        ),
        select_b=(
            "SELECT id, zip_code, state, city, neighborhood, street, number, "
            "complement, created_at, updated_at FROM address"
        ),
        field_map={},
        table_name_a="addresses",
        table_name_b="address",
        pk_a=("id",),
        pk_b=("id",),
    ),
    "storage_files": TableSpec(
        register_a=StorageFileA,
        register_b=StorageFileB,
        table_a=StorageFileTableA,
        table_b=StorageFileTableB,
        select_a="SELECT id, name, path, created_at, updated_at FROM storage_files",
        select_b="SELECT id, name, path, created_at, updated_at FROM storage_file",
        field_map={},
        table_name_a="storage_files",
        table_name_b="storage_file",
        pk_a=("id",),
        pk_b=("id",),
    ),
    "permission_groups": TableSpec(
        register_a=PermissionGroupA,
        register_b=PermissionGroupB,
        table_a=PermissionGroupTableA,
        table_b=PermissionGroupTableB,
        select_a="SELECT id, description, created_at FROM permission_groups",
        select_b="SELECT id, description, created_at FROM permission_group",
        field_map={},
        table_name_a="permission_groups",
        table_name_b="permission_group",
        pk_a=("id",),
        pk_b=("id",),
    ),
    "permissions": TableSpec(
        register_a=PermissionA,
        register_b=PermissionB,
        table_a=PermissionTableA,
        table_b=PermissionTableB,
        select_a=(
            "SELECT id, name, description, url, created_at, updated_at FROM permissions"
        ),
        select_b="SELECT id, name, description, url, created_at, updated_at FROM permission",
        field_map={},
        table_name_a="permissions",
        table_name_b="permission",
        pk_a=("id",),
        pk_b=("id",),
    ),
    "plans": TableSpec(
        register_a=PlanA,
        register_b=PlanB,
        table_a=PlanTableA,
        table_b=PlanTableB,
        select_a=(
            "SELECT id, name, description, price, duration_days, is_active, "
            "created_at, updated_at FROM plans"
        ),
        select_b=(
            "SELECT id, name, description, price, duration_days, is_active, "
            "created_at, updated_at FROM plan"
        ),
        field_map={},
        table_name_a="plans",
        table_name_b="plan",
        pk_a=("id",),
        pk_b=("id",),
    ),
    "companies": TableSpec(
        register_a=EnterpriseA,
        register_b=EnterpriseB,
        table_a=EnterpriseTableA,
        table_b=EnterpriseTableB,
        select_a=(
            "SELECT id, name, trade_name, cnpj, created_at, updated_at, address_id "
            "FROM companies"
        ),
        select_b=(
            "SELECT id, name, trade_name, cnpj, created_at, updated_at, id_address "
            "FROM enterprise"
        ),
        field_map={"address_id": "id_address"},
        table_name_a="companies",
        table_name_b="enterprise",
        pk_a=("id",),
        pk_b=("id",),
    ),
    "units": TableSpec(
        register_a=UnitA,
        register_b=UnitB,
        table_a=UnitTableA,
        table_b=UnitTableB,
        select_a=(
            "SELECT id, cnae, cnpj, is_active, created_at, updated_at, company_id, "
            "address_id FROM units"
        ),
        select_b=(
            "SELECT id, cnae, cnpj, is_active, created_at, updated_at, id_enterprise, "
            "id_address FROM unit"
        ),
        field_map={"company_id": "id_enterprise", "address_id": "id_address"},
        table_name_a="units",
        table_name_b="unit",
        pk_a=("id",),
        pk_b=("id",),
    ),
    "sectors": TableSpec(
        register_a=DepartmentA,
        register_b=DepartmentB,
        table_a=DepartmentTableA,
        table_b=DepartmentTableB,
        select_a=(
            "SELECT id, name, description, created_at, updated_at, unit_id FROM sectors"
        ),
        select_b=(
            "SELECT id, name, description, created_at, updated_at, id_unit FROM department"
        ),
        field_map={"unit_id": "id_unit"},
        table_name_a="sectors",
        table_name_b="department",
        pk_a=("id",),
        pk_b=("id",),
    ),
    "permission_group_permissions": TableSpec(
        register_a=PermissionGroupPermissionA,
        register_b=PermissionGroupPermissionB,
        table_a=PermissionGroupPermissionTableA,
        table_b=PermissionGroupPermissionTableB,
        select_a=(
            "SELECT id, created_at, updated_at, permission_id, permission_group_id "
            "FROM permission_group_permissions"
        ),
        select_b=(
            "SELECT id, created_at, updated_at, id_permission, id_permission_group "
            "FROM permission_group_permission"
        ),
        field_map={
            "permission_id": "id_permission",
            "permission_group_id": "id_permission_group",
        },
        table_name_a="permission_group_permissions",
        table_name_b="permission_group_permission",
        pk_a=("id",),
        pk_b=("id",),
    ),
    "employees": TableSpec(
        register_a=EmployeeA,
        register_b=EmployeeB,
        table_a=EmployeeTableA,
        table_b=EmployeeTableB,
        select_a=(
            "SELECT id, cpf, name, email, phone, password_hash, employee_status, "
            "created_at, updated_at, storage_file_id, sector_id FROM employees"
        ),
        select_b=(
            "SELECT id, cpf, name, email, phone, password_hash, employee_status, "
            "created_at, updated_at, id_storage_file, id_department FROM employee"
        ),
        field_map={
            "storage_file_id": "id_storage_file",
            "sector_id": "id_department",
        },
        table_name_a="employees",
        table_name_b="employee",
        pk_a=("id",),
        pk_b=("id",),
        enum_fields=("employee_status",),
    ),
    "permission_group_employees": TableSpec(
        register_a=PermissionGroupEmployeeA,
        register_b=PermissionGroupEmployeeB,
        table_a=PermissionGroupEmployeeTableA,
        table_b=PermissionGroupEmployeeTableB,
        select_a="SELECT employee_id, permission_group_id FROM permission_group_employees",
        select_b="SELECT id_employee, id_permission_group FROM permission_group_employee",
        field_map={
            "employee_id": "id_employee",
            "permission_group_id": "id_permission_group",
        },
        table_name_a="permission_group_employees",
        table_name_b="permission_group_employee",
        pk_a=("employee_id", "permission_group_id"),
        pk_b=("id_employee", "id_permission_group"),
    ),
    "subscriptions": TableSpec(
        register_a=PlanSubscriptionA,
        register_b=PlanSubscriptionB,
        table_a=PlanSubscriptionTableA,
        table_b=PlanSubscriptionTableB,
        select_a=(
            "SELECT id, is_active, installments, created_at, deactivated_at, plan_id, "
            "company_id FROM subscriptions"
        ),
        select_b=(
            "SELECT id, is_active, installments, created_at, deactivated_at, id_plan, "
            "id_enterprise FROM plan_subscription"
        ),
        field_map={"plan_id": "id_plan", "company_id": "id_enterprise"},
        table_name_a="subscriptions",
        table_name_b="plan_subscription",
        pk_a=("id",),
        pk_b=("id",),
    ),
}

TABLE_DEST = {
    key: (spec.table_name_b, spec.pk_a, spec.pk_b) for key, spec in TABLES.items()
}
