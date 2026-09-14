import select

from src.definition import TABLE_DEST, TABLE_ORDER, TABLES
from src.driver import drive_to_a, drive_to_b

TABLE_DRIVERS = {
    key: (lambda a, b, op, k=key, row_pks=None: drive_to_b(a, b, op, k, row_pks=row_pks))
    for key in TABLES
}
TABLE_ORDER_B = [TABLES[key].table_name_b for key in TABLE_ORDER]
TABLE_DRIVERS_TO_A = {
    spec.table_name_b: (
        lambda source, dest, op, k=key, row_pks=None: drive_to_a(
            dest, source, op, k, row_pks=row_pks
        )
    )
    for key, spec in TABLES.items()
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
    _drain(
        connection_a,
        connection_b,
        TABLE_DRIVERS,
        TABLE_ORDER,
    )


def drain_b_to_a(connection_b, connection_a):
    _drain(
        connection_b,
        connection_a,
        TABLE_DRIVERS_TO_A,
        TABLE_ORDER_B,
    )


def _drain(source, dest, drivers, order):
    rows = fetch_pending(source)
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
    for table_name in order:
        operation = latest_write.get(table_name)
        driver = drivers.get(table_name)
        if operation is None or driver is None:
            continue
        driver(source, dest, operation)
    for table_name in reversed(order):
        payloads = deletes.get(table_name)
        driver = drivers.get(table_name)
        if not payloads or driver is None:
            continue
        driver(source, dest, "delete", row_pks=payloads)
    mark_processed(source, ids)


def listen_once(connection_a, connection_b):
    cursor = connection_a.cursor()
    cursor.execute(LISTEN_SQL)
    notifies = getattr(connection_a, "notifies", None)
    if not notifies:
        return
    drain(connection_a, connection_b)
    notifies.clear()


def wait_for_notify(connection, timeout, select_fn=None, poll_fn=None):
    readable, _, _ = (select_fn or select.select)([connection], [], [], timeout)
    if connection in readable:
        (poll_fn or connection.poll)()
    return bool(getattr(connection, "notifies", None))


def listen_loop(connection, on_notify, should_stop, timeout=1.0, select_fn=None, poll_fn=None):
    while not should_stop():
        if wait_for_notify(
            connection, timeout, select_fn=select_fn, poll_fn=poll_fn
        ):
            on_notify()
            connection.notifies.clear()
