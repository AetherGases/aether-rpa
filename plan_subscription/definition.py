from dataclasses import dataclass
from datetime import datetime


@dataclass
class RegisterA:
    id: int
    is_active: bool
    installments: int
    created_at: datetime
    deactivated_at: datetime | None
    plan_id: int | None
    company_id: int | None


@dataclass
class TableA:
    registers: list[RegisterA]


@dataclass
class RegisterB:
    id: int
    is_active: bool
    installments: int
    created_at: datetime
    deactivated_at: datetime | None
    id_plan: int | None
    id_enterprise: int | None


@dataclass
class TableB:
    registers: list[RegisterB]
