from shared.driver import drive
from .transformer import transform_to_a, transform_to_b

_TABLE_A = "sectors"
_TABLE_B = "department"
_PK = ("id",)


def drive_to_a(connection_a, connection_b, operation):
    drive(connection_a, transform_to_a(connection_b), operation, _TABLE_A, _PK)


def drive_to_b(connection_a, connection_b, operation):
    drive(connection_b, transform_to_b(connection_a), operation, _TABLE_B, _PK)
