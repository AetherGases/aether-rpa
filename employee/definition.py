from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EmployeeStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    IN_VACATION = "IN_VACATION"


@dataclass
class Register:
    id: int
    cpf: str
    name: str
    email: str
    phone: str
    password_hash: str
    employee_status: EmployeeStatus
    created_at: datetime
    updated_at: datetime | None
    id_storage_file: int | None
    id_department: int | None


@dataclass
class Table:
    registers: list[Register]
