from shared.extractor import extract
from .definition import RegisterA, RegisterB, TableA, TableB

_SELECT_A = "SELECT id, name, description, created_at, updated_at, unit_id FROM sectors"
_SELECT_B = "SELECT id, name, description, created_at, updated_at, id_unit FROM department"


def extract_from_a(connection):
    return extract(connection, _SELECT_A, RegisterA, TableA)


def extract_from_b(connection):
    return extract(connection, _SELECT_B, RegisterB, TableB)
