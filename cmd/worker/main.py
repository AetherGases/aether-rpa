import os

from cmd.worker.prepare import prepare
from orchestrator.listener import listen_once


def connect_a(url=None):
    import psycopg2
    return psycopg2.connect(url or os.environ["DATABASE_A_URL"])


def connect_b(url=None):
    import psycopg2
    return psycopg2.connect(url or os.environ["DATABASE_B_URL"])


def run(connection_a, connection_b, prepare_fn, listen_fn):
    prepare_fn(connection_a)
    connection_a.commit()
    listen_fn(connection_a, connection_b)
    connection_a.commit()
    connection_b.commit()


def main(
    connect_a_fn=connect_a,
    connect_b_fn=connect_b,
    prepare_fn=prepare,
    listen_fn=listen_once,
):
    connection_a = connect_a_fn()
    connection_b = connect_b_fn()
    run(connection_a, connection_b, prepare_fn, listen_fn)


if __name__ == "__main__":  # pragma: no cover
    main()
