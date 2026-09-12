from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Register:
    id: int
    name: str
    description: str | None
    price: Decimal
    duration_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


@dataclass
class Table:
    registers: list[Register]
