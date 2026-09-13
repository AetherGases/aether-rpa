from dataclasses import dataclass
from datetime import datetime


@dataclass
class Register:
    id: int
    cnae: str | None
    cnpj: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
    id_enterprise: int | None
    id_address: int | None


@dataclass
class Table:
    registers: list[Register]
