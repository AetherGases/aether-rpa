import logging
import os

from src.definition import TABLE_ORDER, TABLES
from src.orchestrator import (
    LISTEN_SQL,
    drain,
    drain_b_to_a,
    listen_loop,
    listen_once,
    wait_for_notify,
)

LOGGER = logging.getLogger("aether.rpa")
APPLICATION_NAME = "aether-rpa"
SOURCE_TABLES = tuple(TABLE_ORDER)
SOURCE_TABLES_B = tuple(TABLES[key].table_name_b for key in TABLE_ORDER)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS rpa_outbox (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(150) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    row_pk JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
)
"""

CREATE_WRITE_FN = """
CREATE OR REPLACE FUNCTION aether_rpa_enqueue_write() RETURNS trigger AS $$
BEGIN
    IF current_setting('application_name', true) = 'aether-rpa' THEN
        RETURN NULL;
    END IF;
    INSERT INTO rpa_outbox (table_name, operation)
    VALUES (TG_TABLE_NAME, lower(TG_OP));
    PERFORM pg_notify('aether_rpa', TG_TABLE_NAME);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql
"""

CREATE_DELETE_FN = """
CREATE OR REPLACE FUNCTION aether_rpa_enqueue_delete() RETURNS trigger AS $$
BEGIN
    IF current_setting('application_name', true) = 'aether-rpa' THEN
        RETURN OLD;
    END IF;
    INSERT INTO rpa_outbox (table_name, operation, row_pk)
    VALUES (TG_TABLE_NAME, 'delete', to_jsonb(OLD));
    PERFORM pg_notify('aether_rpa', TG_TABLE_NAME);
    RETURN OLD;
END;
$$ LANGUAGE plpgsql
"""


def _trigger_statements(table):
    return [
        f"DROP TRIGGER IF EXISTS aether_rpa_write_{table} ON {table}",
        (
            f"CREATE TRIGGER aether_rpa_write_{table} "
            f"AFTER INSERT OR UPDATE ON {table} "
            f"FOR EACH STATEMENT EXECUTE FUNCTION aether_rpa_enqueue_write()"
        ),
        f"DROP TRIGGER IF EXISTS aether_rpa_delete_{table} ON {table}",
        (
            f"CREATE TRIGGER aether_rpa_delete_{table} "
            f"AFTER DELETE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION aether_rpa_enqueue_delete()"
        ),
    ]


def prepare(connection, tables=None):
    if tables is None:
        tables = SOURCE_TABLES
    cursor = connection.cursor()
    cursor.execute(CREATE_TABLE)
    cursor.execute(CREATE_WRITE_FN)
    cursor.execute(CREATE_DELETE_FN)
    for table in tables:
        for statement in _trigger_statements(table):
            cursor.execute(statement)


def connect_a(url=None):
    import psycopg2
    return psycopg2.connect(
        url or os.environ["DATABASE_A_URL"],
        application_name=APPLICATION_NAME,
    )


def connect_b(url=None):
    import psycopg2
    return psycopg2.connect(
        url or os.environ["DATABASE_B_URL"],
        application_name=APPLICATION_NAME,
    )


def _clear_notifies(connection):
    notifies = getattr(connection, "notifies", None)
    if notifies is not None:
        notifies.clear()


def _replicate(drain_callable, source, dest):
    try:
        try:
            drain_callable(source, dest)
        except Exception:
            source.rollback()
            dest.rollback()
            LOGGER.exception("RPA drain failed; retrying")
            drain_callable(source, dest)
        dest.commit()
        source.commit()
    except Exception:
        source.rollback()
        dest.rollback()
        LOGGER.exception("RPA drain failed")
        raise


def _listen(connection):
    connection.cursor().execute(LISTEN_SQL)


def _run_forever(
    connection_a,
    connection_b,
    should_stop,
    wait_for_notify_fn,
    select_fn,
    poll_fn,
    drain_fn,
    drain_b_to_a_fn,
    timeout,
):
    _listen(connection_a)
    _listen(connection_b)
    while not should_stop():
        if wait_for_notify_fn(
            connection_a, timeout, select_fn=select_fn, poll_fn=poll_fn
        ):
            _replicate(drain_fn, connection_a, connection_b)
            _clear_notifies(connection_a)
        if should_stop():
            break
        if wait_for_notify_fn(
            connection_b, timeout, select_fn=select_fn, poll_fn=poll_fn
        ):
            _replicate(drain_b_to_a_fn, connection_b, connection_a)
            _clear_notifies(connection_b)


def run(
    connection_a,
    connection_b,
    prepare_fn=prepare,
    listen_fn=listen_once,
    drain_fn=drain,
    drain_b_to_a_fn=drain_b_to_a,
    forever=False,
    should_stop=None,
    select_fn=None,
    poll_fn=None,
    wait_for_notify_fn=wait_for_notify,
    listen_loop_fn=listen_loop,
    timeout=1.0,
):
    if should_stop is None:
        should_stop = lambda: False
    try:
        prepare_fn(connection_a)
        connection_a.commit()
        prepare_fn(connection_b, SOURCE_TABLES_B)
        connection_b.commit()
        _replicate(drain_fn, connection_a, connection_b)
        _replicate(drain_b_to_a_fn, connection_b, connection_a)
        if forever:
            _run_forever(
                connection_a,
                connection_b,
                should_stop,
                wait_for_notify_fn,
                select_fn,
                poll_fn,
                drain_fn,
                drain_b_to_a_fn,
                timeout,
            )
        elif listen_fn is not None:
            listen_fn(connection_a, connection_b)
            connection_b.commit()
            connection_a.commit()
    finally:
        connection_a.close()
        connection_b.close()


def main(
    connect_a_fn=connect_a,
    connect_b_fn=connect_b,
    prepare_fn=prepare,
    listen_fn=listen_once,
    drain_fn=drain,
    drain_b_to_a_fn=drain_b_to_a,
    forever=False,
    should_stop=None,
    select_fn=None,
    poll_fn=None,
    wait_for_notify_fn=wait_for_notify,
    listen_loop_fn=listen_loop,
    timeout=1.0,
):
    connection_a = connect_a_fn()
    connection_b = connect_b_fn()
    try:
        run(
            connection_a,
            connection_b,
            prepare_fn=prepare_fn,
            listen_fn=listen_fn,
            drain_fn=drain_fn,
            drain_b_to_a_fn=drain_b_to_a_fn,
            forever=forever,
            should_stop=should_stop,
            select_fn=select_fn,
            poll_fn=poll_fn,
            wait_for_notify_fn=wait_for_notify_fn,
            listen_loop_fn=listen_loop_fn,
            timeout=timeout,
        )
    finally:
        connection_a.close()
        connection_b.close()


if __name__ == "__main__":  # pragma: no cover
    main(forever=True)
