from dataclasses import dataclass
from datetime import datetime


@dataclass
class Register:
    id: int
    name: str
    description: str | None
    url: str
    created_at: datetime
    updated_at: datetime | None


@dataclass
class Table:
    registers: list[Register]
