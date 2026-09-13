from dataclasses import fields
from enum import Enum
from types import SimpleNamespace

from src.definition import TABLES
from src.transformer import transform_to_a, transform_to_b


def drive(connection, table, operation, table_name, pk_fields):
    if operation not in ("insert", "update", "delete"):
        raise ValueError(operation)
    registers = table.registers
    if not registers:
        return
    pk = list(pk_fields)
    if operation == "delete":
        pk_values = [
            tuple(_bind(getattr(register, column)) for column in pk)
            for register in registers
        ]
        delete_rows(connection, table_name, pk, pk_values)
        return
    columns = [field.name for field in fields(registers[0])]
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


def delete_rows(connection, table_name, pk_fields, pk_values):
    if not pk_values:
        return
    pk = list(pk_fields)
    where_sql = " AND ".join(f"{column} = %s" for column in pk)
    query = f"DELETE FROM {table_name} WHERE {where_sql}"
    cursor = connection.cursor()
    cursor.executemany(query, list(pk_values))


def drive_to_b(connection_a, connection_b, operation, table_key, row_pks=None):
    spec = TABLES[table_key]
    if operation == "delete":
        drive(
            connection_b,
            _pk_table(spec.table_b, spec.pk_b, row_pks, spec.pk_a),
            "delete",
            spec.table_name_b,
            spec.pk_b,
        )
        return
    drive(
        connection_b,
        transform_to_b(connection_a, table_key),
        operation,
        spec.table_name_b,
        spec.pk_b,
    )


def drive_to_a(connection_a, connection_b, operation, table_key, row_pks=None):
    spec = TABLES[table_key]
    if operation == "delete":
        drive(
            connection_a,
            _pk_table(spec.table_a, spec.pk_a, row_pks, spec.pk_b),
            "delete",
            spec.table_name_a,
            spec.pk_a,
        )
        return
    drive(
        connection_a,
        transform_to_a(connection_b, table_key),
        operation,
        spec.table_name_a,
        spec.pk_a,
    )


def _pk_table(table_cls, dest_pk, row_pks, source_pk):
    registers = [
        SimpleNamespace(
            **{dest_pk[i]: row_pk[source_pk[i]] for i in range(len(dest_pk))}
        )
        for row_pk in row_pks or []
    ]
    return table_cls(registers=registers)


def _bind(value):
    if isinstance(value, Enum):
        return value.value
    return value
