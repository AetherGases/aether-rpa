import logging
from dataclasses import fields
from enum import Enum
from types import SimpleNamespace

import psycopg2

from src.definition import TABLES
from src.transformer import transform_to_a, transform_to_b

LOGGER = logging.getLogger("aether.rpa")

# Errors caused by one row's data: log the row and keep draining the others.
ROW_ERRORS = (psycopg2.DataError, psycopg2.IntegrityError)


def drive(connection, table, operation, table_name, pk_fields, conflict_exprs=None):
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
    # Insert and update are the same upsert: an update may reach a row B never got.
    columns = [
        field.name
        for field in fields(registers[0])
        if not field.metadata.get("derived")
    ]
    set_columns = [column for column in columns if column not in pk]
    col_sql = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    conflict_sql = ", ".join(pk)
    if set_columns:
        exprs = conflict_exprs or {}
        set_sql = ", ".join(
            f"{column} = {exprs.get(column, f'EXCLUDED.{column}')}"
            for column in set_columns
        )
        on_conflict = f"ON CONFLICT ({conflict_sql}) DO UPDATE SET {set_sql}"
    else:
        on_conflict = f"ON CONFLICT ({conflict_sql}) DO NOTHING"
    query = (
        f"INSERT INTO {table_name} ({col_sql}) VALUES ({placeholders}) "
        f"{on_conflict}"
    )
    cursor = connection.cursor()
    for register in registers:
        row = tuple(_bind(getattr(register, column)) for column in columns)
        error = _in_savepoint(cursor, lambda: cursor.execute(query, row), ROW_ERRORS)
        if error is not None:
            LOGGER.error(
                "RPA skipped %s row %s: %s: %s",
                table_name,
                tuple(getattr(register, column) for column in pk),
                type(error).__name__,
                str(error).strip(),
            )
    if len(pk) == 1:
        _sync_sequence(cursor, table_name, pk[0])


def _in_savepoint(cursor, action, errors):
    """Run `action`; on one of `errors` undo only it and return the error."""
    cursor.execute("SAVEPOINT rpa_isolate")
    try:
        action()
    except errors as error:
        cursor.execute("ROLLBACK TO SAVEPOINT rpa_isolate")
        return error
    cursor.execute("RELEASE SAVEPOINT rpa_isolate")
    return None


def _sync_sequence(cursor, table_name, column):
    """Rows are copied with their ids: move the sequence past them so the
    database's own inserts do not collide."""

    def advance():
        cursor.execute("SELECT pg_get_serial_sequence(%s, %s)", (table_name, column))
        sequence = cursor.fetchone()[0]
        if sequence is not None:
            cursor.execute(
                "SELECT setval(%s, GREATEST("
                f"(SELECT COALESCE(MAX({column}), 1) FROM {table_name}), "
                f"(SELECT last_value FROM {sequence})))",
                (sequence,),
            )

    error = _in_savepoint(cursor, advance, psycopg2.Error)
    if error is not None:
        LOGGER.warning(
            "RPA could not advance the %s.%s sequence: %s",
            table_name,
            column,
            str(error).strip(),
        )


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
        transform_to_b(connection_a, table_key, pks=_ids(row_pks, spec.pk_a)),
        operation,
        spec.table_name_b,
        spec.pk_b,
        conflict_exprs=spec.conflict_b,
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
        transform_to_a(connection_b, table_key, pks=_ids(row_pks, spec.pk_b)),
        operation,
        spec.table_name_a,
        spec.pk_a,
        conflict_exprs=spec.conflict_a,
    )


def _ids(row_pks, source_pk):
    """Ids named by the outbox, or None to refresh the whole table."""
    if row_pks is None:
        return None
    return [row_pk[source_pk[0]] for row_pk in row_pks]


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
