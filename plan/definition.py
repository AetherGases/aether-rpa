from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class RegisterA:
    id: int
    name: str
    description: str | None
    price: Decimal
    duration_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


@dataclass
class TableA:
    registers: list[RegisterA]


@dataclass
class RegisterB:
    id: int
    name: str
    description: str | None
    price: Decimal
    duration_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


@dataclass
class TableB:
    registers: list[RegisterB]
