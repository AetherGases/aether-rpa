import logging
from unittest.mock import MagicMock, call

import pytest

from src.orchestrator import LISTEN_SQL
from src.worker import (
    _listen,
    connect_a,
    connect_b,
    main,
    run,
)
from tests.fake_db import fake_connection

APPLICATION_NAME = "aether-rpa"


def test_run_boot_drains_listen_and_commits_dest_first() -> None:
    connection_a = MagicMock(name="a")
    connection_b = MagicMock(name="b")
    drained = []
    listened = []
    commits = []
    connection_a.commit.side_effect = lambda: commits.append("a")
    connection_b.commit.side_effect = lambda: commits.append("b")

    run(
        connection_a,
        connection_b,
        listen_fn=lambda a, b: listened.append((a, b)),
        drain_fn=lambda a, b: drained.append(("a_to_b", a, b)),
        drain_b_to_a_fn=lambda b, a: drained.append(("b_to_a", b, a)),
        forever=False,
    )

    assert drained == [
        ("a_to_b", connection_a, connection_b),
        ("b_to_a", connection_b, connection_a),
    ]
    assert listened == [(connection_a, connection_b)]
    assert commits == ["b", "a", "a", "b", "b", "a"]
    assert connection_a.commit.call_count == 3
    assert connection_b.commit.call_count == 3
    connection_a.close.assert_called()
    connection_b.close.assert_called()


def test_listen_commits_so_listen_takes_effect() -> None:
    connection = MagicMock()

    _listen(connection)

    assert connection.mock_calls == [
        call.cursor(),
        call.cursor().execute(LISTEN_SQL),
        call.commit(),
    ]


def test_run_skips_listen_fn_when_forever() -> None:
    connection_a = MagicMock()
    connection_b = MagicMock()
    listened = []

    run(
        connection_a,
        connection_b,
        listen_fn=lambda a, b: listened.append((a, b)),
        drain_fn=lambda a, b: None,
        drain_b_to_a_fn=lambda b, a: None,
        forever=True,
        should_stop=lambda: True,
        wait_for_notify_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("should not wait after boot stop")
        ),
    )

    assert listened == []
    connection_a.cursor.return_value.execute.assert_any_call(LISTEN_SQL)
    connection_b.cursor.return_value.execute.assert_any_call(LISTEN_SQL)
    connection_a.close.assert_called()
    connection_b.close.assert_called()


def test_run_forever_one_notify_via_select() -> None:
    connection_a = MagicMock(name="a")
    connection_a.notifies = [object()]
    connection_b = MagicMock(name="b")
    connection_b.notifies = []
    drained = []
    commits = []
    connection_a.commit.side_effect = lambda: commits.append("a")
    connection_b.commit.side_effect = lambda: commits.append("b")
    ticks = {"n": 0}

    def should_stop():
        return ticks["n"] >= 1

    def select_fn(readers, writers, errors, timeout):
        ticks["n"] += 1
        return (readers, [], [])

    def poll_fn():
        return None

    run(
        connection_a,
        connection_b,
        listen_fn=lambda a, b: None,
        drain_fn=lambda a, b: drained.append(("a_to_b", a, b)),
        drain_b_to_a_fn=lambda b, a: drained.append(("b_to_a", b, a)),
        forever=True,
        should_stop=should_stop,
        select_fn=select_fn,
        poll_fn=poll_fn,
    )

    assert drained == [
        ("a_to_b", connection_a, connection_b),
        ("b_to_a", connection_b, connection_a),
        ("a_to_b", connection_a, connection_b),
    ]
    assert commits[-2:] == ["b", "a"]
    connection_a.close.assert_called()
    connection_b.close.assert_called()


def test_run_forever_notify_on_b_commits_a_then_b() -> None:
    connection_a = MagicMock(name="a")
    connection_a.notifies = []
    connection_b = MagicMock(name="b")
    connection_b.notifies = [object()]
    drained = []
    commits = []
    connection_a.commit.side_effect = lambda: commits.append("a")
    connection_b.commit.side_effect = lambda: commits.append("b")
    ticks = {"n": 0}

    def should_stop():
        return ticks["n"] >= 2

    def select_fn(readers, writers, errors, timeout):
        ticks["n"] += 1
        return (readers, [], [])

    run(
        connection_a,
        connection_b,
        listen_fn=lambda a, b: None,
        drain_fn=lambda a, b: drained.append(("a_to_b", a, b)),
        drain_b_to_a_fn=lambda b, a: drained.append(("b_to_a", b, a)),
        forever=True,
        should_stop=should_stop,
        select_fn=select_fn,
        poll_fn=lambda: None,
    )

    assert drained[-1] == ("b_to_a", connection_b, connection_a)
    assert commits[-2:] == ["a", "b"]


def test_run_without_listen_fn_still_boot_drains() -> None:
    connection_a = MagicMock()
    connection_b = MagicMock()
    drained = []

    run(
        connection_a,
        connection_b,
        listen_fn=None,
        drain_fn=lambda a, b: drained.append("a_to_b"),
        drain_b_to_a_fn=lambda b, a: drained.append("b_to_a"),
        forever=False,
    )

    assert drained == ["a_to_b", "b_to_a"]
    connection_a.close.assert_called()
    connection_b.close.assert_called()


def test_run_forever_clears_nothing_when_connection_has_no_notifies() -> None:
    connection_a = MagicMock(spec=["cursor", "commit", "rollback", "close"])
    connection_b = MagicMock(spec=["cursor", "commit", "rollback", "close"])
    ticks = {"n": 0}

    def should_stop():
        return ticks["n"] >= 1

    def wait_fn(connection, timeout, select_fn=None, poll_fn=None):
        ticks["n"] += 1
        return connection is connection_a

    run(
        connection_a,
        connection_b,
        listen_fn=None,
        drain_fn=lambda a, b: None,
        drain_b_to_a_fn=lambda b, a: None,
        forever=True,
        should_stop=should_stop,
        wait_for_notify_fn=wait_fn,
    )

    connection_a.close.assert_called()
    connection_b.close.assert_called()


def test_run_retries_drain_once_then_commits() -> None:
    connection_a = MagicMock()
    connection_b = MagicMock()
    drain_fn = MagicMock(side_effect=[RuntimeError("boom"), None])

    run(
        connection_a,
        connection_b,
        listen_fn=lambda a, b: None,
        drain_fn=drain_fn,
        drain_b_to_a_fn=lambda b, a: None,
        forever=False,
    )

    assert drain_fn.call_count == 2
    connection_a.rollback.assert_called()
    connection_b.rollback.assert_called()
    connection_b.commit.assert_called()
    connection_a.commit.assert_called()
    connection_a.close.assert_called()
    connection_b.close.assert_called()


def test_run_rolls_back_logs_and_reraises_when_drain_keeps_failing(caplog) -> None:
    connection_a = MagicMock()
    connection_b = MagicMock()
    drain_fn = MagicMock(side_effect=RuntimeError("boom"))

    with caplog.at_level(logging.ERROR, logger="aether.rpa"):
        with pytest.raises(RuntimeError, match="boom"):
            run(
                connection_a,
                connection_b,
                listen_fn=lambda a, b: None,
                drain_fn=drain_fn,
                drain_b_to_a_fn=lambda b, a: None,
                forever=False,
            )

    assert drain_fn.call_count == 2
    connection_a.rollback.assert_called()
    connection_b.rollback.assert_called()
    connection_a.close.assert_called()
    connection_b.close.assert_called()
    assert any(record.exc_info for record in caplog.records)
    assert any("aether.rpa" == record.name for record in caplog.records)


def test_main_creates_connections_injects_and_closes() -> None:
    connection_a = MagicMock(name="a")
    connection_b = MagicMock(name="b")
    listened = []

    main(
        connect_a_fn=lambda: connection_a,
        connect_b_fn=lambda: connection_b,
        listen_fn=lambda a, b: listened.append((a, b)),
        drain_fn=lambda a, b: None,
        drain_b_to_a_fn=lambda b, a: None,
        forever=False,
    )

    assert listened == [(connection_a, connection_b)]
    connection_a.close.assert_called()
    connection_b.close.assert_called()


def test_connect_a_and_connect_b_use_env_urls(monkeypatch) -> None:
    import sys

    fake = MagicMock()
    fake.connect.side_effect = ["conn-a", "conn-b"]
    monkeypatch.setitem(sys.modules, "psycopg2", fake)
    monkeypatch.setenv("DATABASE_A_URL", "postgresql://a")
    monkeypatch.setenv("DATABASE_B_URL", "postgresql://b")

    assert connect_a() == "conn-a"
    assert connect_b() == "conn-b"
    fake.connect.assert_any_call("postgresql://a", application_name=APPLICATION_NAME)
    fake.connect.assert_any_call("postgresql://b", application_name=APPLICATION_NAME)


def test_connect_a_and_connect_b_use_postgres_env_when_no_legacy_urls(
    monkeypatch,
) -> None:
    import sys

    fake = MagicMock()
    fake.connect.side_effect = ["conn-a", "conn-b"]
    monkeypatch.setitem(sys.modules, "psycopg2", fake)
    monkeypatch.delenv("DATABASE_A_URL", raising=False)
    monkeypatch.delenv("DATABASE_B_URL", raising=False)
    monkeypatch.delenv("RPA_DATABASE_A_URL", raising=False)
    monkeypatch.delenv("RPA_DATABASE_B_URL", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "u")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p")
    monkeypatch.setenv("POSTGRES_HOST", "cluster")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_SSLMODE", "require")
    monkeypatch.setenv("POSTGRES_DB_FIRST_YEAR", "year_one")
    monkeypatch.setenv("POSTGRES_DB", "year_two")
    monkeypatch.setenv("RPA_POSTGRES_USER", "rpa")
    monkeypatch.setenv("RPA_POSTGRES_PASSWORD", "rp")

    assert connect_a() == "conn-a"
    assert connect_b() == "conn-b"
    fake.connect.assert_any_call(
        "postgresql://rpa:rp@cluster:5432/year_one?sslmode=require",
        application_name=APPLICATION_NAME,
    )
    fake.connect.assert_any_call(
        "postgresql://u:p@cluster:5432/year_two?sslmode=require",
        application_name=APPLICATION_NAME,
    )


def test_connect_a_and_connect_b_use_explicit_url(monkeypatch) -> None:
    import sys

    fake = MagicMock()
    fake.connect.side_effect = ["conn-a", "conn-b"]
    monkeypatch.setitem(sys.modules, "psycopg2", fake)

    assert connect_a("postgresql://explicit-a") == "conn-a"
    assert connect_b("postgresql://explicit-b") == "conn-b"
    fake.connect.assert_any_call(
        "postgresql://explicit-a", application_name=APPLICATION_NAME
    )
    fake.connect.assert_any_call(
        "postgresql://explicit-b", application_name=APPLICATION_NAME
    )
