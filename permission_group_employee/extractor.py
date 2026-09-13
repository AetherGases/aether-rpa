from shared.extractor import extract
from .definition import RegisterA, RegisterB, TableA, TableB

_SELECT_A = "SELECT employee_id, permission_group_id FROM permission_group_employees"
_SELECT_B = "SELECT id_employee, id_permission_group FROM permission_group_employee"


def extract_from_a(connection):
    return extract(connection, _SELECT_A, RegisterA, TableA)


def extract_from_b(connection):
    return extract(connection, _SELECT_B, RegisterB, TableB)
