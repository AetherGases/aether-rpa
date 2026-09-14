from src.definition import TABLES
from src.orchestrator import (
    CHANNEL,
    FETCH_PENDING,
    LISTEN_SQL,
    MARK_PROCESSED,
    TABLE_DEST,
    TABLE_DRIVERS,
    TABLE_DRIVERS_TO_A,
    TABLE_ORDER,
    TABLE_ORDER_B,
    drain,
    drain_b_to_a,
    fetch_pending,
    listen_loop,
    listen_once,
    mark_processed,
    wait_for_notify,
)
from tests.fake_db import fake_connection


def test_table_drivers_maps_all_database_a_tables() -> None:
    assert set(TABLE_DRIVERS) == set(TABLE_ORDER) == set(TABLES)


def test_table_drivers_wrap_drive_to_b_with_table_key(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        "src.orchestrator.drive_to_b",
        lambda a, b, op, k, row_pks=None: calls.append((a, b, op, k, row_pks)),
    )
    connection_a = object()
    connection_b = object()

    TABLE_DRIVERS["companies"](connection_a, connection_b, "insert")

    assert calls == [(connection_a, connection_b, "insert", "companies", None)]


def test_table_order_lists_parents_before_children() -> None:
    assert TABLE_ORDER == [
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
    ]
    assert set(TABLE_ORDER) == set(TABLE_DRIVERS) == set(TABLE_DEST)


def test_table_dest_maps_b_names_and_pks() -> None:
    assert TABLE_DEST["companies"] == ("enterprise", ("id",), ("id",))
    assert TABLE_DEST["permission_group_employees"] == (
        "permission_group_employee",
        ("employee_id", "permission_group_id"),
        ("id_employee", "id_permission_group"),
    )
    assert TABLE_DEST["subscriptions"] == (
        "plan_subscription",
        ("id",),
        ("id",),
    )


def test_fetch_pending_includes_row_pk() -> None:
    connection, cursor = fake_connection(
        ["id", "table_name", "operation", "row_pk"],
        [(1, "companies", "insert", None)],
    )
    rows = fetch_pending(connection)
    cursor.execute.assert_called_once_with(FETCH_PENDING)
    assert rows == [(1, "companies", "insert", None)]


def test_mark_processed_updates_ids() -> None:
    connection, cursor = fake_connection([], [])
    mark_processed(connection, [1, 2])
    cursor.execute.assert_called_once_with(MARK_PROCESSED, ([1, 2],))


def test_mark_processed_empty_ids_does_not_execute() -> None:
    connection, cursor = fake_connection([], [])
    mark_processed(connection, [])
    cursor.execute.assert_not_called()
    connection.cursor.assert_not_called()


def test_drain_insert_update_last_operation_wins(monkeypatch) -> None:
    connection_a, cursor_a = fake_connection(
        ["id", "table_name", "operation", "row_pk"],
        [
            (1, "companies", "insert", None),
            (2, "companies", "update", None),
            (3, "addresses", "insert", None),
        ],
    )
    connection_b, _cursor_b = fake_connection([], [])
    calls = []
    monkeypatch.setattr(
        "src.orchestrator.TABLE_DRIVERS",
        {
            "addresses": lambda a, b, op: calls.append(("addresses", op)),
            "companies": lambda a, b, op: calls.append(("companies", op)),
        },
    )
    monkeypatch.setattr(
        "src.orchestrator.TABLE_ORDER",
        ["addresses", "companies"],
    )
    monkeypatch.setattr("src.orchestrator.TABLE_DEST", {})

    drain(connection_a, connection_b)

    assert calls == [("addresses", "insert"), ("companies", "update")]
    assert cursor_a.execute.call_args_list[-1].args == (MARK_PROCESSED, ([1, 2, 3],))


def test_drain_delete_maps_pk_and_deletes_on_b(monkeypatch) -> None:
    connection_a, cursor_a = fake_connection(
        ["id", "table_name", "operation", "row_pk"],
        [
            (1, "companies", "delete", {"id": 9}),
            (2, "permission_group_employees", "delete", {
                "employee_id": 1,
                "permission_group_id": 2,
            }),
        ],
    )
    connection_b, _cursor_b = fake_connection([], [])
    calls = []
    monkeypatch.setattr(
        "src.orchestrator.TABLE_DRIVERS",
        {
            "companies": lambda a, b, op, row_pks=None: calls.append(
                (op, "companies", row_pks)
            ),
            "permission_group_employees": lambda a, b, op, row_pks=None: calls.append(
                (op, "permission_group_employees", row_pks)
            ),
        },
    )
    monkeypatch.setattr(
        "src.orchestrator.TABLE_ORDER",
        ["companies", "permission_group_employees"],
    )

    drain(connection_a, connection_b)

    assert calls == [
        (
            "delete",
            "permission_group_employees",
            [{"employee_id": 1, "permission_group_id": 2}],
        ),
        ("delete", "companies", [{"id": 9}]),
    ]
    assert cursor_a.execute.call_args_list[-1].args == (MARK_PROCESSED, ([1, 2],))


def test_drain_skips_unknown_table_but_marks_processed(monkeypatch) -> None:
    connection_a, cursor_a = fake_connection(
        ["id", "table_name", "operation", "row_pk"],
        [(1, "not_a_table", "insert", None)],
    )
    connection_b, _cursor_b = fake_connection([], [])
    monkeypatch.setattr("src.orchestrator.TABLE_DRIVERS", {})
    monkeypatch.setattr("src.orchestrator.TABLE_ORDER", [])
    monkeypatch.setattr("src.orchestrator.TABLE_DEST", {})

    drain(connection_a, connection_b)

    assert cursor_a.execute.call_args_list[-1].args == (MARK_PROCESSED, ([1],))


def test_drain_empty_pending_does_not_mark() -> None:
    connection_a, cursor_a = fake_connection(
        ["id", "table_name", "operation", "row_pk"], []
    )
    connection_b, _cursor_b = fake_connection([], [])
    drain(connection_a, connection_b)
    cursor_a.execute.assert_called_once_with(FETCH_PENDING)


def test_listen_once_without_notify_does_not_drain(monkeypatch) -> None:
    connection_a, cursor_a = fake_connection([], [])
    connection_a.notifies = []
    connection_b, _cursor_b = fake_connection([], [])
    drained = []
    monkeypatch.setattr(
        "src.orchestrator.drain",
        lambda a, b: drained.append((a, b)),
    )
    listen_once(connection_a, connection_b)
    cursor_a.execute.assert_called_once_with(LISTEN_SQL)
    assert drained == []
    assert CHANNEL == "aether_rpa"


def test_listen_once_with_notify_drains_and_clears(monkeypatch) -> None:
    connection_a, cursor_a = fake_connection([], [])
    connection_a.notifies = [object()]
    connection_b, _cursor_b = fake_connection([], [])
    drained = []
    monkeypatch.setattr(
        "src.orchestrator.drain",
        lambda a, b: drained.append((a, b)),
    )
    listen_once(connection_a, connection_b)
    assert drained == [(connection_a, connection_b)]
    assert connection_a.notifies == []


def test_table_drivers_to_a_maps_b_names_and_swaps_connections(monkeypatch) -> None:
    assert set(TABLE_DRIVERS_TO_A) == {spec.table_name_b for spec in TABLES.values()}
    assert TABLE_ORDER_B == [TABLES[key].table_name_b for key in TABLE_ORDER]
    calls = []
    monkeypatch.setattr(
        "src.orchestrator.drive_to_a",
        lambda dest, source, op, k, row_pks=None: calls.append(
            (dest, source, op, k, row_pks)
        ),
    )
    source = object()
    dest = object()

    TABLE_DRIVERS_TO_A["enterprise"](source, dest, "insert")

    assert calls == [(dest, source, "insert", "companies", None)]


def test_drain_b_to_a_last_write_wins_and_marks_source_b(monkeypatch) -> None:
    connection_b, cursor_b = fake_connection(
        ["id", "table_name", "operation", "row_pk"],
        [
            (1, "enterprise", "insert", None),
            (2, "enterprise", "update", None),
            (3, "address", "insert", None),
        ],
    )
    connection_a, _cursor_a = fake_connection([], [])
    calls = []
    monkeypatch.setattr(
        "src.orchestrator.TABLE_DRIVERS_TO_A",
        {
            "address": lambda source, dest, op: calls.append(("address", op)),
            "enterprise": lambda source, dest, op: calls.append(("enterprise", op)),
        },
    )
    monkeypatch.setattr(
        "src.orchestrator.TABLE_ORDER_B",
        ["address", "enterprise"],
    )

    drain_b_to_a(connection_b, connection_a)

    assert calls == [("address", "insert"), ("enterprise", "update")]
    assert cursor_b.execute.call_args_list[-1].args == (MARK_PROCESSED, ([1, 2, 3],))


def test_drain_b_to_a_delete_passes_row_pks_in_reverse_order(monkeypatch) -> None:
    connection_b, cursor_b = fake_connection(
        ["id", "table_name", "operation", "row_pk"],
        [
            (1, "enterprise", "delete", {"id": 9}),
            (2, "permission_group_employee", "delete", {
                "id_employee": 1,
                "id_permission_group": 2,
            }),
        ],
    )
    connection_a, _cursor_a = fake_connection([], [])
    calls = []
    monkeypatch.setattr(
        "src.orchestrator.TABLE_DRIVERS_TO_A",
        {
            "enterprise": lambda source, dest, op, row_pks=None: calls.append(
                (op, "enterprise", row_pks)
            ),
            "permission_group_employee": lambda source, dest, op, row_pks=None: calls.append(
                (op, "permission_group_employee", row_pks)
            ),
        },
    )
    monkeypatch.setattr(
        "src.orchestrator.TABLE_ORDER_B",
        ["enterprise", "permission_group_employee"],
    )

    drain_b_to_a(connection_b, connection_a)

    assert calls == [
        (
            "delete",
            "permission_group_employee",
            [{"id_employee": 1, "id_permission_group": 2}],
        ),
        ("delete", "enterprise", [{"id": 9}]),
    ]
    assert cursor_b.execute.call_args_list[-1].args == (MARK_PROCESSED, ([1, 2],))


def test_drain_b_to_a_skips_unknown_table_but_marks_processed(monkeypatch) -> None:
    connection_b, cursor_b = fake_connection(
        ["id", "table_name", "operation", "row_pk"],
        [(1, "not_a_table", "insert", None)],
    )
    connection_a, _cursor_a = fake_connection([], [])
    monkeypatch.setattr("src.orchestrator.TABLE_DRIVERS_TO_A", {})
    monkeypatch.setattr("src.orchestrator.TABLE_ORDER_B", [])

    drain_b_to_a(connection_b, connection_a)

    assert cursor_b.execute.call_args_list[-1].args == (MARK_PROCESSED, ([1],))


def test_drain_b_to_a_empty_pending_does_not_mark() -> None:
    connection_b, cursor_b = fake_connection(
        ["id", "table_name", "operation", "row_pk"], []
    )
    connection_a, _cursor_a = fake_connection([], [])
    drain_b_to_a(connection_b, connection_a)
    cursor_b.execute.assert_called_once_with(FETCH_PENDING)


def test_wait_for_notify_true_when_readable_and_notifies() -> None:
    polled = []
    connection = type("Conn", (), {})()
    connection.notifies = [object()]

    def select_fn(readers, writers, errors, timeout):
        assert readers == [connection]
        assert writers == []
        assert errors == []
        assert timeout == 2.0
        return ([connection], [], [])

    def poll_fn():
        polled.append(True)

    assert wait_for_notify(connection, 2.0, select_fn=select_fn, poll_fn=poll_fn) is True
    assert polled == [True]


def test_wait_for_notify_false_when_not_readable() -> None:
    polled = []
    connection = type("Conn", (), {})()
    connection.notifies = []

    def select_fn(readers, writers, errors, timeout):
        return ([], [], [])

    def poll_fn():
        polled.append(True)

    assert wait_for_notify(
        connection, 1.0, select_fn=select_fn, poll_fn=poll_fn
    ) is False
    assert polled == []


def test_wait_for_notify_defaults_to_select_and_poll(monkeypatch) -> None:
    connection = type("Conn", (), {})()
    connection.notifies = []

    def poll():
        connection.notifies.append(object())

    connection.poll = poll
    monkeypatch.setattr(
        "src.orchestrator.select.select",
        lambda readers, writers, errors, timeout: ([connection], [], []),
    )

    assert wait_for_notify(connection, 0.1) is True


def test_listen_loop_stops_when_should_stop_flips_after_one_notify() -> None:
    connection = type("Conn", (), {})()
    connection.notifies = [object()]
    calls = []

    def on_notify():
        calls.append("notify")

    def should_stop():
        return len(calls) >= 1

    def select_fn(readers, writers, errors, timeout):
        return ([connection], [], [])

    def poll_fn():
        return None

    listen_loop(
        connection,
        on_notify,
        should_stop,
        timeout=0.01,
        select_fn=select_fn,
        poll_fn=poll_fn,
    )

    assert calls == ["notify"]
    assert connection.notifies == []


def test_listen_loop_skips_on_notify_when_wait_is_false() -> None:
    connection = type("Conn", (), {})()
    connection.notifies = []
    ticks = {"n": 0}

    def should_stop():
        ticks["n"] += 1
        return ticks["n"] > 2

    def on_notify():
        raise AssertionError("on_notify should not run")

    def select_fn(readers, writers, errors, timeout):
        return ([], [], [])

    listen_loop(
        connection,
        on_notify,
        should_stop,
        timeout=0.01,
        select_fn=select_fn,
        poll_fn=lambda: None,
    )

    assert ticks["n"] == 3
