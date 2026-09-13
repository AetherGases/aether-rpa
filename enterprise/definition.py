from dataclasses import dataclass
from datetime import datetime


@dataclass
class Register:
    id: int
    name: str
    trade_name: str | None
    cnpj: str
    created_at: datetime
    updated_at: datetime | None
    id_address: int | None


@dataclass
class Table:
    registers: list[Register]
