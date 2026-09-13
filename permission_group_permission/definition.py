from dataclasses import dataclass
from datetime import datetime


@dataclass
class RegisterA:
    id: int
    created_at: datetime
    updated_at: datetime | None
    permission_id: int | None
    permission_group_id: int | None


@dataclass
class TableA:
    registers: list[RegisterA]


@dataclass
class RegisterB:
    id: int
    created_at: datetime
    updated_at: datetime | None
    id_permission: int | None
    id_permission_group: int | None


@dataclass
class TableB:
    registers: list[RegisterB]
