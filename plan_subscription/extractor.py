from shared.extractor import extract
from .definition import RegisterA, RegisterB, TableA, TableB

_SELECT_A = (
    "SELECT id, is_active, installments, created_at, deactivated_at, plan_id, "
    "company_id FROM subscriptions"
)
_SELECT_B = (
    "SELECT id, is_active, installments, created_at, deactivated_at, id_plan, "
    "id_enterprise FROM plan_subscription"
)


def extract_from_a(connection):
    return extract(connection, _SELECT_A, RegisterA, TableA)


def extract_from_b(connection):
    return extract(connection, _SELECT_B, RegisterB, TableB)
