from dataclasses import dataclass
from datetime import datetime


@dataclass
class RegisterA:
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    unit_id: int | None


@dataclass
class TableA:
    registers: list[RegisterA]


@dataclass
class RegisterB:
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    id_unit: int | None


@dataclass
class TableB:
    registers: list[RegisterB]
