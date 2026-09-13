from shared.driver import drive
from .transformer import transform_to_a, transform_to_b


def drive_to_a(connection_a, connection_b, operation):
    return drive(
        connection_a,
        transform_to_a(connection_b),
        operation,
        "permission_group_permissions",
        ("id",),
    )


def drive_to_b(connection_a, connection_b, operation):
    return drive(
        connection_b,
        transform_to_b(connection_a),
        operation,
        "permission_group_permission",
        ("id",),
    )
