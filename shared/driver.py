from dataclasses import fields
from enum import Enum


def drive(connection, table, operation, table_name, pk_fields):
    if operation not in ("insert", "update"):
        raise ValueError(operation)
    registers = table.registers
    if not registers:
        return
    columns = [field.name for field in fields(registers[0])]
    pk = list(pk_fields)
    if operation == "update":
        set_columns = [column for column in columns if column not in pk]
        if not set_columns:
            return
        set_sql = ", ".join(f"{column} = %s" for column in set_columns)
        where_sql = " AND ".join(f"{column} = %s" for column in pk)
        query = f"UPDATE {table_name} SET {set_sql} WHERE {where_sql}"
        bind_columns = set_columns + pk
    else:
        col_sql = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO {table_name} ({col_sql}) VALUES ({placeholders})"
        bind_columns = columns
    rows = [
        tuple(_bind(getattr(register, column)) for column in bind_columns)
        for register in registers
    ]
    cursor = connection.cursor()
    cursor.executemany(query, rows)


def _bind(value):
    if isinstance(value, Enum):
        return value.value
    return value
