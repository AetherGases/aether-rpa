from shared.extractor import extract
from .definition import EmployeeStatus, RegisterA, RegisterB, TableA, TableB

_SELECT_A = (
    "SELECT id, cpf, name, email, phone, password_hash, employee_status, "
    "created_at, updated_at, storage_file_id, sector_id FROM employees"
)
_SELECT_B = (
    "SELECT id, cpf, name, email, phone, password_hash, employee_status, "
    "created_at, updated_at, id_storage_file, id_department FROM employee"
)


def extract_from_a(connection):
    table = extract(connection, _SELECT_A, RegisterA, TableA)
    for register in table.registers:
        register.employee_status = EmployeeStatus(register.employee_status)
    return table


def extract_from_b(connection):
    table = extract(connection, _SELECT_B, RegisterB, TableB)
    for register in table.registers:
        register.employee_status = EmployeeStatus(register.employee_status)
    return table
