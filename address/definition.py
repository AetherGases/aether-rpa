from dataclasses import dataclass
from datetime import datetime


@dataclass
class RegisterA:
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
class TableA:
    registers: list[RegisterA]


@dataclass
class RegisterB:
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
class TableB:
    registers: list[RegisterB]
