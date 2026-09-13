from shared.driver import drive
from .transformer import transform_to_a, transform_to_b


def drive_to_a(connection_a, connection_b, operation):
    drive(connection_a, transform_to_a(connection_b), operation, "addresses", ("id",))


def drive_to_b(connection_a, connection_b, operation):
    drive(connection_b, transform_to_b(connection_a), operation, "address", ("id",))
