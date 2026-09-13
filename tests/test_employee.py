from datetime import datetime

from employee import EmployeeStatus, RegisterA, RegisterB, TableA, TableB
from employee.driver import drive_to_a, drive_to_b
from employee.extractor import extract_from_a, extract_from_b
from employee.transformer import transform_to_a, transform_to_b
from tests.fake_db import fake_connection

CREATED_AT = datetime(2026, 9, 12, 14, 0, 0)


def test_register_b_and_table_b_hold_employee_fields() -> None:
    register = RegisterB(
        id=1,
        cpf="12345678901",
        name="Ana Silva",
        email="ana@example.com",
        phone="11999999999",
        password_hash="hash",
        employee_status=EmployeeStatus.ACTIVE,
        created_at=CREATED_AT,
        updated_at=None,
        id_storage_file=None,
        id_department=None,
    )
    table = TableB(registers=[register])

    assert table.registers == [register]
    assert register.employee_status is EmployeeStatus.ACTIVE
    assert register.id_storage_file is None
    assert register.id_department is None


def test_register_a_and_table_a_hold_employee_fields() -> None:
    register = RegisterA(
        id=1,
        cpf="12345678901",
        name="Ana Silva",
        email="ana@example.com",
        phone="11999999999",
        password_hash="hash",
        employee_status=EmployeeStatus.ACTIVE,
        created_at=CREATED_AT,
        updated_at=None,
        storage_file_id=None,
        sector_id=None,
    )
    table = TableA(registers=[register])

    assert table.registers == [register]
    assert register.storage_file_id is None
    assert register.sector_id is None
    assert not hasattr(register, "id_department")


def test_employee_status_matches_database_b_values() -> None:
    assert EmployeeStatus.ACTIVE.value == "ACTIVE"
    assert EmployeeStatus.INACTIVE.value == "INACTIVE"
    assert EmployeeStatus.IN_VACATION.value == "IN_VACATION"


def test_table_b_accepts_empty_registers() -> None:
    table = TableB(registers=[])

    assert table.registers == []


def test_table_a_accepts_empty_registers() -> None:
    table = TableA(registers=[])

    assert table.registers == []


COLUMNS_A = [
    "id",
    "cpf",
    "name",
    "email",
    "phone",
    "password_hash",
    "employee_status",
    "created_at",
    "updated_at",
    "storage_file_id",
    "sector_id",
]
COLUMNS_B = [
    "id",
    "cpf",
    "name",
    "email",
    "phone",
    "password_hash",
    "employee_status",
    "created_at",
    "updated_at",
    "id_storage_file",
    "id_department",
]
SELECT_A = (
    "SELECT id, cpf, name, email, phone, password_hash, employee_status, "
    "created_at, updated_at, storage_file_id, sector_id FROM employees"
)
SELECT_B = (
    "SELECT id, cpf, name, email, phone, password_hash, employee_status, "
    "created_at, updated_at, id_storage_file, id_department FROM employee"
)
ROW_A = (
    1,
    "12345678901",
    "Ana Silva",
    "ana@example.com",
    "11999999999",
    "hash",
    "ACTIVE",
    CREATED_AT,
    None,
    5,
    6,
)
ROW_B = (
    1,
    "12345678901",
    "Ana Silva",
    "ana@example.com",
    "11999999999",
    "hash",
    "IN_VACATION",
    CREATED_AT,
    None,
    5,
    6,
)


def test_extract_from_a_fills_register_a_with_employee_status() -> None:
    connection, cursor = fake_connection(COLUMNS_A, [ROW_A])

    table = extract_from_a(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert table == TableA(
        registers=[
            RegisterA(
                id=1,
                cpf="12345678901",
                name="Ana Silva",
                email="ana@example.com",
                phone="11999999999",
                password_hash="hash",
                employee_status=EmployeeStatus.ACTIVE,
                created_at=CREATED_AT,
                updated_at=None,
                storage_file_id=5,
                sector_id=6,
            )
        ]
    )


def test_extract_from_b_fills_register_b_with_employee_status() -> None:
    connection, cursor = fake_connection(COLUMNS_B, [ROW_B])

    table = extract_from_b(connection)

    cursor.execute.assert_called_once_with(SELECT_B)
    assert table == TableB(
        registers=[
            RegisterB(
                id=1,
                cpf="12345678901",
                name="Ana Silva",
                email="ana@example.com",
                phone="11999999999",
                password_hash="hash",
                employee_status=EmployeeStatus.IN_VACATION,
                created_at=CREATED_AT,
                updated_at=None,
                id_storage_file=5,
                id_department=6,
            )
        ]
    )


def test_extract_from_a_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_A, [])

    assert extract_from_a(connection) == TableA(registers=[])


def test_extract_from_b_empty_rows() -> None:
    connection, _cursor = fake_connection(COLUMNS_B, [])

    assert extract_from_b(connection) == TableB(registers=[])


def test_transform_to_b_remaps_storage_file_and_sector_ids() -> None:
    connection, cursor = fake_connection(COLUMNS_A, [ROW_A])

    result = transform_to_b(connection)

    cursor.execute.assert_called_once_with(SELECT_A)
    assert result == TableB(
        registers=[
            RegisterB(
                id=1,
                cpf="12345678901",
                name="Ana Silva",
                email="ana@example.com",
                phone="11999999999",
                password_hash="hash",
                employee_status=EmployeeStatus.ACTIVE,
                created_at=CREATED_AT,
                updated_at=None,
                id_storage_file=5,
                id_department=6,
            )
        ]
    )


def test_transform_to_a_remaps_storage_file_and_department_ids() -> None:
    connection, cursor = fake_connection(COLUMNS_B, [ROW_B])

    result = transform_to_a(connection)

    cursor.execute.assert_called_once_with(SELECT_B)
    assert result == TableA(
        registers=[
            RegisterA(
                id=1,
                cpf="12345678901",
                name="Ana Silva",
                email="ana@example.com",
                phone="11999999999",
                password_hash="hash",
                employee_status=EmployeeStatus.IN_VACATION,
                created_at=CREATED_AT,
                updated_at=None,
                storage_file_id=5,
                sector_id=6,
            )
        ]
    )


def test_transform_to_b_empty_registers() -> None:
    connection, _cursor = fake_connection(COLUMNS_A, [])

    assert transform_to_b(connection) == TableB(registers=[])


def test_transform_to_a_empty_registers() -> None:
    connection, _cursor = fake_connection(COLUMNS_B, [])

    assert transform_to_a(connection) == TableA(registers=[])


def test_drive_to_b_insert() -> None:
    connection_a, _cursor_a = fake_connection(COLUMNS_A, [ROW_A])
    connection_b, cursor_b = fake_connection(COLUMNS_B, [])

    drive_to_b(connection_a, connection_b, "insert")

    cursor_b.executemany.assert_called_once_with(
        "INSERT INTO employee (id, cpf, name, email, phone, password_hash, "
        "employee_status, created_at, updated_at, id_storage_file, id_department) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        [
            (
                1,
                "12345678901",
                "Ana Silva",
                "ana@example.com",
                "11999999999",
                "hash",
                "ACTIVE",
                CREATED_AT,
                None,
                5,
                6,
            )
        ],
    )


def test_drive_to_a_update() -> None:
    connection_a, cursor_a = fake_connection(COLUMNS_A, [])
    connection_b, _cursor_b = fake_connection(COLUMNS_B, [ROW_B])

    drive_to_a(connection_a, connection_b, "update")

    cursor_a.executemany.assert_called_once_with(
        "UPDATE employees SET cpf = %s, name = %s, email = %s, phone = %s, "
        "password_hash = %s, employee_status = %s, created_at = %s, updated_at = %s, "
        "storage_file_id = %s, sector_id = %s WHERE id = %s",
        [
            (
                "12345678901",
                "Ana Silva",
                "ana@example.com",
                "11999999999",
                "hash",
                "IN_VACATION",
                CREATED_AT,
                None,
                5,
                6,
                1,
            )
        ],
    )


def test_drive_to_b_empty_no_op() -> None:
    connection_a, _cursor_a = fake_connection(COLUMNS_A, [])
    connection_b, cursor_b = fake_connection(COLUMNS_B, [])

    drive_to_b(connection_a, connection_b, "insert")

    cursor_b.executemany.assert_not_called()
    connection_b.cursor.assert_not_called()
