from dataclasses import dataclass
from datetime import datetime


@dataclass
class RegisterA:
    id: int
    cnae: str | None
    cnpj: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
    company_id: int | None
    address_id: int | None


@dataclass
class TableA:
    registers: list[RegisterA]


@dataclass
class RegisterB:
    id: int
    cnae: str | None
    cnpj: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
    id_enterprise: int | None
    id_address: int | None


@dataclass
class TableB:
    registers: list[RegisterB]
