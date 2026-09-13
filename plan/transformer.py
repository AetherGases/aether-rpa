from shared.transformer import transform
from .definition import RegisterA, RegisterB, TableA, TableB
from .extractor import extract_from_a, extract_from_b

FIELD_MAP = {}


def transform_to_b(connection):
    return transform(extract_from_a(connection), RegisterB, TableB, FIELD_MAP)


def transform_to_a(connection):
    return transform(extract_from_b(connection), RegisterA, TableA, FIELD_MAP)
