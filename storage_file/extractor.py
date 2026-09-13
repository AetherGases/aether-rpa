from shared.extractor import extract
from .definition import RegisterA, RegisterB, TableA, TableB

_SELECT_A = "SELECT id, name, path, created_at, updated_at FROM storage_files"
_SELECT_B = "SELECT id, name, path, created_at, updated_at FROM storage_file"


def extract_from_a(connection):
    return extract(connection, _SELECT_A, RegisterA, TableA)


def extract_from_b(connection):
    return extract(connection, _SELECT_B, RegisterB, TableB)
