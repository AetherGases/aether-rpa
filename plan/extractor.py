from shared.extractor import extract
from .definition import RegisterA, RegisterB, TableA, TableB

_SELECT_A = (
    "SELECT id, name, description, price, duration_days, is_active, "
    "created_at, updated_at FROM plans"
)
_SELECT_B = (
    "SELECT id, name, description, price, duration_days, is_active, "
    "created_at, updated_at FROM plan"
)


def extract_from_a(connection):
    return extract(connection, _SELECT_A, RegisterA, TableA)


def extract_from_b(connection):
    return extract(connection, _SELECT_B, RegisterB, TableB)
