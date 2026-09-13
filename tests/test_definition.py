from datetime import datetime
from decimal import Decimal

from src.definition import (
    TABLES,
    TABLE_DEST,
    TABLE_ORDER,
    AddressA,
    AddressB,
    AddressTableA,
    AddressTableB,
    DepartmentA,
    DepartmentB,
    EmployeeA,
    EmployeeB,
    EmployeeStatus,
    EnterpriseA,
    EnterpriseB,
    PermissionA,
    PermissionB,
    PermissionGroupA,
    PermissionGroupB,
    PermissionGroupEmployeeA,
    PermissionGroupEmployeeB,
    PermissionGroupPermissionA,
    PermissionGroupPermissionB,
    PlanA,
    PlanB,
    PlanSubscriptionA,
    PlanSubscriptionB,
    StorageFileA,
    StorageFileB,
    TableSpec,
    UnitA,
    UnitB,
)

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


def test_table_order_lists_parents_before_children() -> None:
    assert TABLE_ORDER == [
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
    assert set(TABLE_ORDER) == set(TABLES) == set(TABLE_DEST)


def test_tables_catalog_uses_table_spec() -> None:
    spec = TABLES["addresses"]
    assert isinstance(spec, TableSpec)
    assert spec.register_a is AddressA
    assert spec.register_b is AddressB
    assert spec.table_a is AddressTableA
    assert spec.table_b is AddressTableB
    assert spec.table_name_a == "addresses"
    assert spec.table_name_b == "address"
    assert spec.pk_a == ("id",)
    assert spec.pk_b == ("id",)
    assert spec.field_map == {}
    assert spec.enum_fields == ()
    assert "FROM addresses" in spec.select_a
    assert "FROM address" in spec.select_b


def test_divergent_field_maps_and_names() -> None:
    assert TABLES["companies"].field_map == {"address_id": "id_address"}
    assert TABLES["companies"].table_name_b == "enterprise"
    assert TABLES["units"].field_map == {
        "company_id": "id_enterprise",
        "address_id": "id_address",
    }
    assert TABLES["sectors"].field_map == {"unit_id": "id_unit"}
    assert TABLES["sectors"].table_name_a == "sectors"
    assert TABLES["sectors"].table_name_b == "department"
    assert TABLES["employees"].field_map == {
        "storage_file_id": "id_storage_file",
        "sector_id": "id_department",
    }
    assert TABLES["employees"].enum_fields == ("employee_status",)
    assert TABLES["permission_group_permissions"].field_map == {
        "permission_id": "id_permission",
        "permission_group_id": "id_permission_group",
    }
    assert TABLES["permission_group_employees"].field_map == {
        "employee_id": "id_employee",
        "permission_group_id": "id_permission_group",
    }
    assert TABLES["permission_group_employees"].pk_a == (
        "employee_id",
        "permission_group_id",
    )
    assert TABLES["permission_group_employees"].pk_b == (
        "id_employee",
        "id_permission_group",
    )
    assert TABLES["subscriptions"].field_map == {
        "plan_id": "id_plan",
        "company_id": "id_enterprise",
    }
    assert TABLES["subscriptions"].table_name_a == "subscriptions"
    assert TABLES["subscriptions"].table_name_b == "plan_subscription"


def test_identical_schema_tables_have_empty_field_map() -> None:
    for key in (
        "addresses",
        "storage_files",
        "permission_groups",
        "permissions",
        "plans",
    ):
        assert TABLES[key].field_map == {}


def test_table_dest_maps_b_names_and_pks() -> None:
    assert TABLE_DEST["companies"] == ("enterprise", ("id",), ("id",))
    assert TABLE_DEST["permission_group_employees"] == (
        "permission_group_employee",
        ("employee_id", "permission_group_id"),
        ("id_employee", "id_permission_group"),
    )
    assert TABLE_DEST["subscriptions"] == (
        "plan_subscription",
        ("id",),
        ("id",),
    )


def test_employee_status_matches_database_b_values() -> None:
    assert EmployeeStatus.ACTIVE.value == "ACTIVE"
    assert EmployeeStatus.INACTIVE.value == "INACTIVE"
    assert EmployeeStatus.IN_VACATION.value == "IN_VACATION"


def test_prefixed_registers_hold_a_and_b_fields() -> None:
    address_a = AddressA(
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
    address_b = AddressB(
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
    enterprise_a = EnterpriseA(
        id=1,
        name="ACME",
        trade_name=None,
        cnpj="123",
        created_at=CREATED_AT,
        updated_at=None,
        address_id=1,
    )
    enterprise_b = EnterpriseB(
        id=1,
        name="ACME",
        trade_name=None,
        cnpj="123",
        created_at=CREATED_AT,
        updated_at=None,
        id_address=1,
    )
    unit_a = UnitA(
        id=1,
        cnae=None,
        cnpj="123",
        is_active=True,
        created_at=CREATED_AT,
        updated_at=None,
        company_id=1,
        address_id=1,
    )
    unit_b = UnitB(
        id=1,
        cnae=None,
        cnpj="123",
        is_active=True,
        created_at=CREATED_AT,
        updated_at=None,
        id_enterprise=1,
        id_address=1,
    )
    department_a = DepartmentA(
        id=1,
        name="Ops",
        description=None,
        created_at=CREATED_AT,
        updated_at=None,
        unit_id=1,
    )
    department_b = DepartmentB(
        id=1,
        name="Ops",
        description=None,
        created_at=CREATED_AT,
        updated_at=None,
        id_unit=1,
    )
    storage_a = StorageFileA(
        id=1, name="a", path="/a", created_at=CREATED_AT, updated_at=None
    )
    storage_b = StorageFileB(
        id=1, name="a", path="/a", created_at=CREATED_AT, updated_at=None
    )
    group_a = PermissionGroupA(id=1, description="admin", created_at=CREATED_AT)
    group_b = PermissionGroupB(id=1, description="admin", created_at=CREATED_AT)
    permission_a = PermissionA(
        id=1,
        name="read",
        description=None,
        url="/r",
        created_at=CREATED_AT,
        updated_at=None,
    )
    permission_b = PermissionB(
        id=1,
        name="read",
        description=None,
        url="/r",
        created_at=CREATED_AT,
        updated_at=None,
    )
    pgp_a = PermissionGroupPermissionA(
        id=1,
        created_at=CREATED_AT,
        updated_at=None,
        permission_id=1,
        permission_group_id=1,
    )
    pgp_b = PermissionGroupPermissionB(
        id=1,
        created_at=CREATED_AT,
        updated_at=None,
        id_permission=1,
        id_permission_group=1,
    )
    employee_a = EmployeeA(
        id=1,
        cpf="12345678901",
        name="Ana",
        email="ana@example.com",
        phone="11999999999",
        password_hash="hash",
        employee_status=EmployeeStatus.ACTIVE,
        created_at=CREATED_AT,
        updated_at=None,
        storage_file_id=None,
        sector_id=None,
    )
    employee_b = EmployeeB(
        id=1,
        cpf="12345678901",
        name="Ana",
        email="ana@example.com",
        phone="11999999999",
        password_hash="hash",
        employee_status=EmployeeStatus.ACTIVE,
        created_at=CREATED_AT,
        updated_at=None,
        id_storage_file=None,
        id_department=None,
    )
    pge_a = PermissionGroupEmployeeA(employee_id=1, permission_group_id=2)
    pge_b = PermissionGroupEmployeeB(id_employee=1, id_permission_group=2)
    plan_a = PlanA(
        id=1,
        name="Pro",
        description=None,
        price=Decimal("10.00"),
        duration_days=30,
        is_active=True,
        created_at=CREATED_AT,
        updated_at=None,
    )
    plan_b = PlanB(
        id=1,
        name="Pro",
        description=None,
        price=Decimal("10.00"),
        duration_days=30,
        is_active=True,
        created_at=CREATED_AT,
        updated_at=None,
    )
    sub_a = PlanSubscriptionA(
        id=1,
        is_active=True,
        installments=1,
        created_at=CREATED_AT,
        deactivated_at=None,
        plan_id=1,
        company_id=1,
    )
    sub_b = PlanSubscriptionB(
        id=1,
        is_active=True,
        installments=1,
        created_at=CREATED_AT,
        deactivated_at=None,
        id_plan=1,
        id_enterprise=1,
    )

    assert AddressTableA(registers=[address_a]).registers == [address_a]
    assert AddressTableB(registers=[address_b]).registers == [address_b]
    assert enterprise_a.address_id == enterprise_b.id_address == 1
    assert unit_a.company_id == unit_b.id_enterprise == 1
    assert department_a.unit_id == department_b.id_unit == 1
    assert storage_a.path == storage_b.path == "/a"
    assert group_a.description == group_b.description
    assert permission_a.url == permission_b.url
    assert pgp_a.permission_id == pgp_b.id_permission == 1
    assert employee_a.sector_id is employee_b.id_department is None
    assert pge_a.employee_id == pge_b.id_employee == 1
    assert plan_a.price == plan_b.price
    assert sub_a.company_id == sub_b.id_enterprise == 1
    assert TABLES["companies"].register_a is EnterpriseA
    assert TABLES["sectors"].register_b is DepartmentB
    assert TABLES["employees"].register_a is EmployeeA
    assert TABLES["subscriptions"].register_b is PlanSubscriptionB
