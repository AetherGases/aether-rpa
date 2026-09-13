from shared.transformer import transform
from .definition import RegisterA, RegisterB, TableA, TableB
from .extractor import extract_from_a, extract_from_b

FIELD_MAP = {"storage_file_id": "id_storage_file", "sector_id": "id_department"}


def transform_to_b(connection):
    return transform(extract_from_a(connection), RegisterB, TableB, FIELD_MAP)


def transform_to_a(connection):
    return transform(
        extract_from_b(connection),
        RegisterA,
        TableA,
        {v: k for k, v in FIELD_MAP.items()},
    )
