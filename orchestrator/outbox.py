from shared.driver import delete_rows

from .registry import TABLE_DEST, TABLE_DRIVERS, TABLE_ORDER

FETCH_PENDING = (
    "SELECT id, table_name, operation, row_pk FROM rpa_outbox "
    "WHERE processed_at IS NULL ORDER BY id"
)
MARK_PROCESSED = (
    "UPDATE rpa_outbox SET processed_at = CURRENT_TIMESTAMP WHERE id = ANY(%s)"
)


def fetch_pending(connection):
    cursor = connection.cursor()
    cursor.execute(FETCH_PENDING)
    return cursor.fetchall()


def mark_processed(connection, ids):
    if not ids:
        return
    cursor = connection.cursor()
    cursor.execute(MARK_PROCESSED, (list(ids),))


def _pk_tuple(row_pk, pk_a):
    return tuple(row_pk[column] for column in pk_a)


def drain(connection_a, connection_b):
    rows = fetch_pending(connection_a)
    if not rows:
        return
    ids = []
    latest_write = {}
    deletes = {}
    for row_id, table_name, operation, row_pk in rows:
        ids.append(row_id)
        if operation == "delete":
            deletes.setdefault(table_name, []).append(row_pk)
        else:
            latest_write[table_name] = operation
    for table_name in TABLE_ORDER:
        operation = latest_write.get(table_name)
        driver = TABLE_DRIVERS.get(table_name)
        if operation is None or driver is None:
            continue
        driver(connection_a, connection_b, operation)
    for table_name in reversed(TABLE_ORDER):
        payloads = deletes.get(table_name)
        dest = TABLE_DEST.get(table_name)
        if not payloads or dest is None:
            continue
        table_b, pk_a, pk_b = dest
        values = [_pk_tuple(row_pk, pk_a) for row_pk in payloads]
        delete_rows(connection_b, table_b, pk_b, values)
    mark_processed(connection_a, ids)
