from shared.transformer import transform
from .definition import RegisterA, RegisterB, TableA, TableB

FIELD_MAP = {
    "employee_id": "id_employee",
    "permission_group_id": "id_permission_group",
}


def transform_to_b(table):
    return transform(table, RegisterB, TableB, FIELD_MAP)


def transform_to_a(table):
    return transform(table, RegisterA, TableA, {v: k for k, v in FIELD_MAP.items()})
