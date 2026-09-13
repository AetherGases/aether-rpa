from datetime import datetime

from permission_group_permission import RegisterA, RegisterB, TableA, TableB
from permission_group_permission.extractor import extract_from_a, extract_from_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


def test_register_b_and_table_b_hold_permission_group_permission_fields() -> None:
    register = RegisterB(
        id=1,
        created_at=CREATED_AT,
        updated_at=None,
        id_permission=None,
        id_permission_group=None,
    )
    table = TableB(registers=[register])

    assert table.registers == [register]
    assert register.id_permission is None
    assert register.id_permission_group is None


def test_register_a_and_table_a_hold_permission_group_permission_fields() -> None:
    register = RegisterA(
        id=1,
        created_at=CREATED_AT,
        updated_at=None,
        permission_id=None,
        permission_group_id=None,
    )
    table = TableA(registers=[register])

    assert table.registers == [register]
    assert register.permission_id is None
    assert register.permission_group_id is None
    assert not hasattr(register, "id_permission")


def test_table_b_accepts_empty_registers() -> None:
    table = TableB(registers=[])

    assert table.registers == []


def test_table_a_accepts_empty_registers() -> None:
    table = TableA(registers=[])

    assert table.registers == []


COLUMNS_A = ["id", "created_at", "updated_at", "permission_id", "permission_group_id"]
COLUMNS_B = ["id", "created_at", "updated_at", "id_permission", "id_permission_group"]
SELECT_A = (
    "SELECT id, created_at, updated_at, permission_id, permission_group_id "
    "FROM permission_group_permissions"
)
SELECT_B = (
    "SELECT id, created_at, updated_at, id_permission, id_permission_group "
    "FROM permission_group_permission"
)
ROW = (1, CREATED_AT, None, 8, 9)


def test_extract_from_a_fills_register_a() -> None:
    connection, cursor = fake_connection(COLUMNS_A, [ROW])

    table = extract_from_a(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert table == TableA(
        registers=[
            RegisterA(
                id=1,
                created_at=CREATED_AT,
                updated_at=None,
                permission_id=8,
                permission_group_id=9,
            )
        ]
    )


def test_extract_from_b_fills_register_b() -> None:
    connection, cursor = fake_connection(COLUMNS_B, [ROW])

    table = extract_from_b(connection)

    cursor.execute.assert_called_once_with(SELECT_B)
    assert table == TableB(
        registers=[
            RegisterB(
                id=1,
                created_at=CREATED_AT,
                updated_at=None,
                id_permission=8,
                id_permission_group=9,
            )
        ]
    )


def test_extract_from_a_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_A, [])

    assert extract_from_a(connection) == TableA(registers=[])


def test_extract_from_b_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_B, [])

    assert extract_from_b(connection) == TableB(registers=[])


from permission_group_permission.transformer import transform_to_a, transform_to_b


def test_transform_to_b_remaps_permission_ids() -> None:
    table = TableA(
        registers=[
            RegisterA(
                id=1,
                created_at=CREATED_AT,
                updated_at=None,
                permission_id=7,
                permission_group_id=8,
            )
        ]
    )
    result = transform_to_b(table)
    assert result == TableB(
        registers=[
            RegisterB(
                id=1,
                created_at=CREATED_AT,
                updated_at=None,
                id_permission=7,
                id_permission_group=8,
            )
        ]
    )


def test_transform_to_a_remaps_permission_ids() -> None:
    table = TableB(
        registers=[
            RegisterB(
                id=1,
                created_at=CREATED_AT,
                updated_at=None,
                id_permission=7,
                id_permission_group=8,
            )
        ]
    )
    result = transform_to_a(table)
    assert result == TableA(
        registers=[
            RegisterA(
                id=1,
                created_at=CREATED_AT,
                updated_at=None,
                permission_id=7,
                permission_group_id=8,
            )
        ]
    )


def test_transform_to_b_empty_registers() -> None:
    assert transform_to_b(TableA(registers=[])) == TableB(registers=[])


def test_transform_to_a_empty_registers() -> None:
    assert transform_to_a(TableB(registers=[])) == TableA(registers=[])
