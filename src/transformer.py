from dataclasses import fields

from src.definition import TABLES, TransformError
from src.extractor import extract_from_a, extract_from_b


def transform(table, register_cls, table_cls, field_map, table_key, to_b):
    registers = []
    for source in table.registers:
        kwargs = {
            field_map.get(field.name, field.name): getattr(source, field.name)
            for field in fields(source)
        }
        kwargs = _apply_conversions(kwargs, table_key, to_b)
        registers.append(register_cls(**kwargs))
    return table_cls(registers=registers)


def transform_to_b(connection, table_key):
    spec = TABLES[table_key]
    return transform(
        extract_from_a(connection, table_key),
        spec.register_b,
        spec.table_b,
        spec.field_map,
        table_key,
        True,
    )


def transform_to_a(connection, table_key):
    spec = TABLES[table_key]
    inverse = {v: k for k, v in spec.field_map.items()}
    return transform(
        extract_from_b(connection, table_key),
        spec.register_a,
        spec.table_a,
        inverse,
        table_key,
        False,
    )


def _apply_conversions(kwargs, table_key, to_b):
    if table_key == "addresses":
        if to_b:
            kwargs["number"] = _address_number_a_to_b(kwargs.get("number"))
        else:
            kwargs["number"] = _address_number_b_to_a(kwargs.get("number"))
    elif table_key == "subscriptions":
        if to_b:
            kwargs["installments"] = _installments_a_to_b(kwargs.get("installments"))
        else:
            kwargs["installments"] = _installments_b_to_a(kwargs.get("installments"))
    return kwargs


def _address_number_a_to_b(value):
    if value is None:
        raise TransformError("address number cannot be null")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise TransformError(f"address number is not numeric: {value!r}") from exc


def _address_number_b_to_a(value):
    if value is None:
        raise TransformError("address number cannot be null")
    return str(value)


def _installments_a_to_b(value):
    if value is None:
        raise TransformError("installments cannot be null in A")
    return 1 if value else 0


def _installments_b_to_a(value):
    if value is None:
        raise TransformError("installments cannot be null in B")
    return value > 0
