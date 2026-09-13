from shared.extractor import extract
from .definition import RegisterA, RegisterB, TableA, TableB

_SELECT_A = "SELECT id, description, created_at FROM permission_groups"
_SELECT_B = "SELECT id, description, created_at FROM permission_group"


def extract_from_a(connection):
    return extract(connection, _SELECT_A, RegisterA, TableA)


def extract_from_b(connection):
    return extract(connection, _SELECT_B, RegisterB, TableB)
