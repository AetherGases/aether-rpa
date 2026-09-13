from dataclasses import dataclass
from datetime import datetime


@dataclass
class RegisterA:
    id: int
    description: str
    created_at: datetime


@dataclass
class TableA:
    registers: list[RegisterA]


@dataclass
class RegisterB:
    id: int
    description: str
    created_at: datetime


@dataclass
class TableB:
    registers: list[RegisterB]
