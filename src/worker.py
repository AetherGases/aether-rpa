import logging

from src.db_url import resolve_database_a_url, resolve_database_b_url
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


def connect_a(url=None):
    import psycopg2
    return psycopg2.connect(
        resolve_database_a_url(url),
        application_name=APPLICATION_NAME,
    )


def connect_b(url=None):
    import psycopg2
    return psycopg2.connect(
        resolve_database_b_url(url),
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
    # LISTEN only takes effect on commit; an open transaction is also killed by idle_in_transaction_session_timeout.
    connection.commit()


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
