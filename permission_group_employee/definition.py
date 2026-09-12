from dataclasses import dataclass


@dataclass
class Register:
    id_employee: int
    id_permission_group: int


@dataclass
class Table:
    registers: list[Register]
