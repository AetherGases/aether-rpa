from shared.extractor import extract
from .definition import RegisterA, RegisterB, TableA, TableB

_SELECT_A = (
    "SELECT id, name, trade_name, cnpj, created_at, updated_at, address_id FROM companies"
)
_SELECT_B = (
    "SELECT id, name, trade_name, cnpj, created_at, updated_at, id_address FROM enterprise"
)


def extract_from_a(connection):
    return extract(connection, _SELECT_A, RegisterA, TableA)


def extract_from_b(connection):
    return extract(connection, _SELECT_B, RegisterB, TableB)
