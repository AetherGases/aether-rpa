from dataclasses import dataclass


@dataclass
class RegisterA:
    employee_id: int
    permission_group_id: int


@dataclass
class TableA:
    registers: list[RegisterA]


@dataclass
class RegisterB:
    id_employee: int
    id_permission_group: int


@dataclass
class TableB:
    registers: list[RegisterB]
