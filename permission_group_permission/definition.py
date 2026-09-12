from dataclasses import dataclass
from datetime import datetime


@dataclass
class Register:
    id: int
    created_at: datetime
    updated_at: datetime | None
    id_permission: int | None
    id_permission_group: int | None


@dataclass
class Table:
    registers: list[Register]
