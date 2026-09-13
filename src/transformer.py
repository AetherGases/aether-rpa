from dataclasses import fields

from src.definition import TABLES
from src.extractor import extract_from_a, extract_from_b


def transform(table, register_cls, table_cls, field_map):
    registers = []
    for source in table.registers:
        kwargs = {
            field_map.get(field.name, field.name): getattr(source, field.name)
            for field in fields(source)
        }
        registers.append(register_cls(**kwargs))
    return table_cls(registers=registers)


def transform_to_b(connection, table_key):
    spec = TABLES[table_key]
    return transform(
        extract_from_a(connection, table_key),
        spec.register_b,
        spec.table_b,
        spec.field_map,
    )


def transform_to_a(connection, table_key):
    spec = TABLES[table_key]
    inverse = {v: k for k, v in spec.field_map.items()}
    return transform(
        extract_from_b(connection, table_key),
        spec.register_a,
        spec.table_a,
        inverse,
    )
