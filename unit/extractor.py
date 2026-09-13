from shared.extractor import extract
from .definition import RegisterA, RegisterB, TableA, TableB

_SELECT_A = (
    "SELECT id, cnae, cnpj, is_active, created_at, updated_at, company_id, "
    "address_id FROM units"
)
_SELECT_B = (
    "SELECT id, cnae, cnpj, is_active, created_at, updated_at, id_enterprise, "
    "id_address FROM unit"
)


def extract_from_a(connection):
    return extract(connection, _SELECT_A, RegisterA, TableA)


def extract_from_b(connection):
    return extract(connection, _SELECT_B, RegisterB, TableB)
