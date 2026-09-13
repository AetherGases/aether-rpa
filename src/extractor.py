from src.definition import TABLES, EmployeeStatus


def extract(connection, query, register_cls, table_cls):
    cursor = connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    registers = [
        register_cls(
            **{cursor.description[i][0]: value for i, value in enumerate(row)}
        )
        for row in rows
    ]
    return table_cls(registers=registers)


def extract_from_a(connection, table_key):
    spec = TABLES[table_key]
    table = extract(connection, spec.select_a, spec.register_a, spec.table_a)
    _coerce_enums(table, spec.enum_fields)
    return table


def extract_from_b(connection, table_key):
    spec = TABLES[table_key]
    table = extract(connection, spec.select_b, spec.register_b, spec.table_b)
    _coerce_enums(table, spec.enum_fields)
    return table


def _coerce_enums(table, enum_fields):
    for field_name in enum_fields:
        for register in table.registers:
            setattr(register, field_name, EmployeeStatus(getattr(register, field_name)))
