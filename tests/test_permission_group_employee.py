from permission_group_employee import RegisterA, RegisterB, TableA, TableB
from permission_group_employee.extractor import extract_from_a, extract_from_b
from tests.fake_db import fake_connection


def test_register_b_and_table_b_hold_permission_group_employee_fields() -> None:
    register = RegisterB(id_employee=1, id_permission_group=2)
    table = TableB(registers=[register])

    assert table.registers == [register]
    assert register.id_employee == 1
    assert register.id_permission_group == 2
    assert not hasattr(register, "id")


def test_register_a_and_table_a_hold_permission_group_employee_fields() -> None:
    register = RegisterA(employee_id=1, permission_group_id=2)
    table = TableA(registers=[register])

    assert table.registers == [register]
    assert register.employee_id == 1
    assert register.permission_group_id == 2
    assert not hasattr(register, "id_employee")


def test_table_b_accepts_empty_registers() -> None:
    table = TableB(registers=[])

    assert table.registers == []


def test_table_a_accepts_empty_registers() -> None:
    table = TableA(registers=[])

    assert table.registers == []


COLUMNS_A = ["employee_id", "permission_group_id"]
COLUMNS_B = ["id_employee", "id_permission_group"]
SELECT_A = "SELECT employee_id, permission_group_id FROM permission_group_employees"
SELECT_B = "SELECT id_employee, id_permission_group FROM permission_group_employee"
ROW = (1, 2)


def test_extract_from_a_fills_register_a() -> None:
    connection, cursor = fake_connection(COLUMNS_A, [ROW])

    table = extract_from_a(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert table == TableA(
        registers=[RegisterA(employee_id=1, permission_group_id=2)]
    )


def test_extract_from_b_fills_register_b() -> None:
    connection, cursor = fake_connection(COLUMNS_B, [ROW])

    table = extract_from_b(connection)

    cursor.execute.assert_called_once_with(SELECT_B)
    assert table == TableB(
        registers=[RegisterB(id_employee=1, id_permission_group=2)]
    )


def test_extract_from_a_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_A, [])

    assert extract_from_a(connection) == TableA(registers=[])


def test_extract_from_b_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_B, [])

    assert extract_from_b(connection) == TableB(registers=[])
