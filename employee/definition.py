from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EmployeeStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    IN_VACATION = "IN_VACATION"


@dataclass
class RegisterA:
    id: int
    cpf: str
    name: str
    email: str
    phone: str
    password_hash: str
    employee_status: EmployeeStatus
    created_at: datetime
    updated_at: datetime | None
    storage_file_id: int | None
    sector_id: int | None


@dataclass
class TableA:
    registers: list[RegisterA]


@dataclass
class RegisterB:
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
class TableB:
    registers: list[RegisterB]
