from dataclasses import dataclass
from datetime import datetime


@dataclass
class RegisterA:
    id: int
    name: str
    trade_name: str | None
    cnpj: str
    created_at: datetime
    updated_at: datetime | None
    address_id: int | None


@dataclass
class TableA:
    registers: list[RegisterA]


@dataclass
class RegisterB:
    id: int
    name: str
    trade_name: str | None
    cnpj: str
    created_at: datetime
    updated_at: datetime | None
    id_address: int | None


@dataclass
class TableB:
    registers: list[RegisterB]
