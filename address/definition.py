from dataclasses import dataclass
from datetime import datetime


@dataclass
class Register:
    id: int
    zip_code: str | None
    state: str
    city: str
    neighborhood: str
    street: str
    number: int
    complement: str | None
    created_at: datetime
    updated_at: datetime | None


@dataclass
class Table:
    registers: list[Register]
