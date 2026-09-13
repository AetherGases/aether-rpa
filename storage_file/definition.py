from dataclasses import dataclass
from datetime import datetime


@dataclass
class RegisterA:
    id: int
    name: str
    path: str
    created_at: datetime
    updated_at: datetime | None


@dataclass
class TableA:
    registers: list[RegisterA]


@dataclass
class RegisterB:
    id: int
    name: str
    path: str
    created_at: datetime
    updated_at: datetime | None


@dataclass
class TableB:
    registers: list[RegisterB]
