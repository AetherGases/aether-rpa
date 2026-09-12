from dataclasses import dataclass
from datetime import datetime


@dataclass
class Register:
    id: int
    is_active: bool
    installments: int
    created_at: datetime
    deactivated_at: datetime | None
    id_plan: int | None
    id_enterprise: int | None


@dataclass
class Table:
    registers: list[Register]
