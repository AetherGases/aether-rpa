from dataclasses import dataclass
from datetime import datetime


@dataclass
class Register:
    id: int
    description: str
    created_at: datetime


@dataclass
class Table:
    registers: list[Register]
