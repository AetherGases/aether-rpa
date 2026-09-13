from shared.extractor import extract
from .definition import RegisterA, RegisterB, TableA, TableB

_SELECT_A = (
    "SELECT id, zip_code, state, city, neighborhood, street, number, "
    "complement, created_at, updated_at FROM addresses"
)
_SELECT_B = (
    "SELECT id, zip_code, state, city, neighborhood, street, number, "
    "complement, created_at, updated_at FROM address"
)


def extract_from_a(connection):
    return extract(connection, _SELECT_A, RegisterA, TableA)


def extract_from_b(connection):
    return extract(connection, _SELECT_B, RegisterB, TableB)
