from enum import Enum

from src.definition import TABLES


def extract(connection, query, register_cls, table_cls, params=None):
    cursor = connection.cursor()
    if params is None:
        cursor.execute(query)
    else:
        cursor.execute(query, params)
    rows = cursor.fetchall()
    registers = [
        register_cls(
            **{cursor.description[i][0]: value for i, value in enumerate(row)}
        )
        for row in rows
    ]
    return table_cls(registers=registers)


def _restrict(select, column, pks):
    """Limit a select to the given primary keys; None keeps the whole table."""
    if pks is None:
        return select, None
    return f"{select} WHERE {column} = ANY(%s)", (list(pks),)


def extract_from_a(connection, table_key, pks=None):
    spec = TABLES[table_key]
    query, params = _restrict(spec.select_a, spec.filter_a, pks)
    table = extract(connection, query, spec.register_a, spec.table_a, params)
    _coerce_enums(table, spec.enum_coercions_a)
    return table


def extract_from_b(connection, table_key, pks=None):
    spec = TABLES[table_key]
    query, params = _restrict(spec.select_b, spec.filter_b, pks)
    table = extract(connection, query, spec.register_b, spec.table_b, params)
    _coerce_enums(table, spec.enum_coercions_b)
    return table


def _coerce_enums(table, enum_coercions: dict[str, type[Enum]]):
    for field_name, enum_cls in enum_coercions.items():
        for register in table.registers:
            value = getattr(register, field_name)
            if value is not None and not isinstance(value, enum_cls):
                try:
                    setattr(register, field_name, enum_cls(value))
                except ValueError:
                    pass
