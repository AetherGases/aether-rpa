from address.driver import drive_to_b as address_to_b
from department.driver import drive_to_b as department_to_b
from employee.driver import drive_to_b as employee_to_b
from enterprise.driver import drive_to_b as enterprise_to_b
from permission.driver import drive_to_b as permission_to_b
from permission_group.driver import drive_to_b as permission_group_to_b
from permission_group_employee.driver import drive_to_b as pge_to_b
from permission_group_permission.driver import drive_to_b as pgp_to_b
from plan.driver import drive_to_b as plan_to_b
from plan_subscription.driver import drive_to_b as plan_subscription_to_b
from storage_file.driver import drive_to_b as storage_file_to_b
from unit.driver import drive_to_b as unit_to_b

TABLE_DRIVERS = {
    "addresses": address_to_b,
    "companies": enterprise_to_b,
    "units": unit_to_b,
    "sectors": department_to_b,
    "storage_files": storage_file_to_b,
    "permission_groups": permission_group_to_b,
    "permissions": permission_to_b,
    "permission_group_permissions": pgp_to_b,
    "employees": employee_to_b,
    "permission_group_employees": pge_to_b,
    "plans": plan_to_b,
    "subscriptions": plan_subscription_to_b,
}

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

TABLE_DEST = {
    "addresses": ("address", ("id",), ("id",)),
    "companies": ("enterprise", ("id",), ("id",)),
    "units": ("unit", ("id",), ("id",)),
    "sectors": ("department", ("id",), ("id",)),
    "storage_files": ("storage_file", ("id",), ("id",)),
    "permission_groups": ("permission_group", ("id",), ("id",)),
    "permissions": ("permission", ("id",), ("id",)),
    "permission_group_permissions": ("permission_group_permission", ("id",), ("id",)),
    "employees": ("employee", ("id",), ("id",)),
    "permission_group_employees": (
        "permission_group_employee",
        ("employee_id", "permission_group_id"),
        ("id_employee", "id_permission_group"),
    ),
    "plans": ("plan", ("id",), ("id",)),
    "subscriptions": ("plan_subscription", ("id",), ("id",)),
}
