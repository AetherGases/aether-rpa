from dataclasses import dataclass
from datetime import datetime


@dataclass
class Register:
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    id_unit: int | None


@dataclass
class Table:
    registers: list[Register]
