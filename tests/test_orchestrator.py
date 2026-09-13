from src.definition import TABLES
from src.orchestrator import (
    CHANNEL,
    FETCH_PENDING,
    LISTEN_SQL,
    MARK_PROCESSED,
    TABLE_DEST,
    TABLE_DRIVERS,
    TABLE_ORDER,
    drain,
    fetch_pending,
    listen_once,
    mark_processed,
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
