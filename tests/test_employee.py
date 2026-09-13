from datetime import datetime

from employee import EmployeeStatus, Register, Table


def test_register_and_table_hold_employee_fields() -> None:
    created_at = datetime(2026, 9, 12, 14, 0, 0)
    register = Register(
        id=1,
        cpf="12345678901",
        name="Ana Silva",
        email="ana@example.com",
        phone="11999999999",
        password_hash="hash",
        employee_status=EmployeeStatus.ACTIVE,
        created_at=created_at,
        updated_at=None,
        id_storage_file=None,
        id_department=None,
    )
    table = Table(registers=[register])

    assert table.registers == [register]
    assert register.employee_status is EmployeeStatus.ACTIVE
    assert register.id_storage_file is None
    assert register.id_department is None


def test_employee_status_matches_database_b_values() -> None:
    assert EmployeeStatus.ACTIVE.value == "ACTIVE"
    assert EmployeeStatus.INACTIVE.value == "INACTIVE"
    assert EmployeeStatus.IN_VACATION.value == "IN_VACATION"


def test_table_accepts_empty_registers() -> None:
    table = Table(registers=[])

    assert table.registers == []
