import logging
import re
from dataclasses import fields

from src.definition import TABLES, TransformError
from src.extractor import extract_from_a, extract_from_b

LOGGER = logging.getLogger("aether.rpa")

CNAE_DIGITS = 7
# B stores the address number as integer; more digits than this could overflow it.
ADDRESS_NUMBER_MAX_DIGITS = 9


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


def transform_to_b(connection, table_key, pks=None):
    spec = TABLES[table_key]
    return transform(
        extract_from_a(connection, table_key, pks),
        spec.register_b,
        spec.table_b,
        spec.field_map,
        table_key,
        True,
    )


def transform_to_a(connection, table_key, pks=None):
    spec = TABLES[table_key]
    inverse = {v: k for k, v in spec.field_map.items()}
    return transform(
        extract_from_b(connection, table_key, pks),
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
    elif table_key == "units":
        if to_b:
            kwargs["cnae"] = _cnae_a_to_b(kwargs.get("cnae"))
        else:
            kwargs["cnae"] = _cnae_b_to_a(kwargs.get("cnae"))
    if to_b:
        _truncate(kwargs, TABLES[table_key].truncate_b, table_key)
    return kwargs


def _truncate(kwargs, limits, table_key):
    for column, limit in limits.items():
        value = kwargs.get(column)
        if isinstance(value, str) and len(value) > limit:
            LOGGER.warning(
                "%s.%s of id %s has %d characters; B accepts %d, truncating",
                table_key,
                column,
                kwargs.get("id"),
                len(value),
                limit,
            )
            kwargs[column] = value[:limit]


def _cnae_a_to_b(value):
    if value is None:
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) == CNAE_DIGITS:
        return digits
    LOGGER.warning("CNAE %r is not %d digits; B gets NULL", value, CNAE_DIGITS)
    return None


def _cnae_b_to_a(value):
    return value.strip() if isinstance(value, str) else value


def _address_number_a_to_b(value):
    if value is None:
        raise TransformError("address number cannot be null")
    match = re.search(r"\d+", str(value))
    if match and len(match.group()) <= ADDRESS_NUMBER_MAX_DIGITS:
        return int(match.group())
    LOGGER.warning("address number %r has no usable digits; B gets 0", value)
    return 0


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
