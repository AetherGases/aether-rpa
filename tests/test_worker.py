from cmd.worker.prepare import SOURCE_TABLES, prepare
from tests.fake_db import fake_connection


def test_prepare_creates_event_table_functions_and_triggers() -> None:
    connection, cursor = fake_connection([], [])

    prepare(connection)

    scripts = [call.args[0] for call in cursor.execute.call_args_list]
    joined = "\n".join(scripts)
    assert "CREATE TABLE IF NOT EXISTS rpa_outbox" in joined
    assert "row_pk JSONB" in joined
    assert "aether_rpa_enqueue_write" in joined
    assert "aether_rpa_enqueue_delete" in joined
    assert "to_jsonb(OLD)" in joined
    assert "pg_notify('aether_rpa'" in joined
    for table in SOURCE_TABLES:
        assert f"ON {table}" in joined
        assert f"aether_rpa_write_{table}" in joined
        assert f"aether_rpa_delete_{table}" in joined
    assert "AFTER INSERT OR UPDATE" in joined
    assert "AFTER DELETE" in joined
    assert SOURCE_TABLES == (
        "addresses",
        "storage_files",
        "permission_groups",
        "permissions",
        "plans",
        "companies",
        "units",
        "sectors",
        "permission_group_permissions",
        "employees",
        "permission_group_employees",
        "subscriptions",
    )


def test_prepare_is_safe_to_run_twice() -> None:
    connection, cursor = fake_connection([], [])
    prepare(connection)
    first = cursor.execute.call_count
    prepare(connection)
    assert cursor.execute.call_count == first * 2


from unittest.mock import MagicMock

from cmd.worker.main import main, run


def test_run_injects_connections_into_prepare_and_listen() -> None:
    connection_a = MagicMock()
    connection_b = MagicMock()
    prepared = []
    listened = []

    run(
        connection_a,
        connection_b,
        prepare_fn=lambda conn: prepared.append(conn),
        listen_fn=lambda a, b: listened.append((a, b)),
    )

    assert prepared == [connection_a]
    assert listened == [(connection_a, connection_b)]
    assert connection_a.commit.call_count == 2
    connection_b.commit.assert_called_once_with()


def test_main_creates_connections_and_injects_them() -> None:
    connection_a = MagicMock(name="a")
    connection_b = MagicMock(name="b")
    prepared = []
    listened = []

    main(
        connect_a_fn=lambda: connection_a,
        connect_b_fn=lambda: connection_b,
        prepare_fn=lambda conn: prepared.append(conn),
        listen_fn=lambda a, b: listened.append((a, b)),
    )

    assert prepared == [connection_a]
    assert listened == [(connection_a, connection_b)]


def test_connect_a_and_connect_b_use_env_urls(monkeypatch) -> None:
    import sys

    from cmd.worker.main import connect_a, connect_b

    fake = MagicMock()
    fake.connect.side_effect = ["conn-a", "conn-b"]
    monkeypatch.setitem(sys.modules, "psycopg2", fake)
    monkeypatch.setenv("DATABASE_A_URL", "postgresql://a")
    monkeypatch.setenv("DATABASE_B_URL", "postgresql://b")

    assert connect_a() == "conn-a"
    assert connect_b() == "conn-b"
    fake.connect.assert_any_call("postgresql://a")
    fake.connect.assert_any_call("postgresql://b")


def test_cmd_package_exposes_stdlib_cmd_attrs() -> None:
    import cmd as cmd_pkg

    assert cmd_pkg.Cmd is not None
    assert cmd_pkg.IDENTCHARS == cmd_pkg.Cmd.identchars
