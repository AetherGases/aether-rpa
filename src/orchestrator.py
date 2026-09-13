from src.definition import TABLE_DEST, TABLE_ORDER, TABLES
from src.driver import drive_to_b

TABLE_DRIVERS = {
    key: (lambda a, b, op, k=key, row_pks=None: drive_to_b(a, b, op, k, row_pks=row_pks))
    for key in TABLES
}

FETCH_PENDING = (
    "SELECT id, table_name, operation, row_pk FROM rpa_outbox "
    "WHERE processed_at IS NULL ORDER BY id"
)
MARK_PROCESSED = (
    "UPDATE rpa_outbox SET processed_at = CURRENT_TIMESTAMP WHERE id = ANY(%s)"
)

CHANNEL = "aether_rpa"
LISTEN_SQL = "LISTEN aether_rpa"


def fetch_pending(connection):
    cursor = connection.cursor()
    cursor.execute(FETCH_PENDING)
    return cursor.fetchall()


def mark_processed(connection, ids):
    if not ids:
        return
    cursor = connection.cursor()
    cursor.execute(MARK_PROCESSED, (list(ids),))


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
        driver = TABLE_DRIVERS.get(table_name)
        if not payloads or driver is None:
            continue
        driver(connection_a, connection_b, "delete", row_pks=payloads)
    mark_processed(connection_a, ids)


def listen_once(connection_a, connection_b):
    cursor = connection_a.cursor()
    cursor.execute(LISTEN_SQL)
    notifies = getattr(connection_a, "notifies", None)
    if not notifies:
        return
    drain(connection_a, connection_b)
    notifies.clear()
