import os
from urllib.parse import quote_plus


def build_postgres_url(dbname: str, user=None, password=None) -> str:
    user = user or os.environ["POSTGRES_USER"]
    password = password or os.environ["POSTGRES_PASSWORD"]
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]
    sslmode = os.environ.get("POSTGRES_SSLMODE", "require")
    safe_user = quote_plus(user)
    safe_password = quote_plus(password)
    safe_sslmode = quote_plus(sslmode)
    return (
        f"postgresql://{safe_user}:{safe_password}@{host}:{port}/{dbname}"
        f"?sslmode={safe_sslmode}"
    )


def resolve_database_a_url(url=None) -> str:
    if url:
        return url
    # RPA_DATABASE_*_URL point to the direct (non-pooler) host: LISTEN does not survive a transaction-mode pooler.
    legacy = os.environ.get("RPA_DATABASE_A_URL") or os.environ.get("DATABASE_A_URL")
    if legacy:
        return legacy
    # The first-year database is accessed through its dedicated RPA role.
    return build_postgres_url(
        os.environ["POSTGRES_DB_FIRST_YEAR"],
        os.environ["RPA_POSTGRES_USER"],
        os.environ["RPA_POSTGRES_PASSWORD"],
    )


def resolve_database_b_url(url=None) -> str:
    if url:
        return url
    legacy = os.environ.get("RPA_DATABASE_B_URL") or os.environ.get("DATABASE_B_URL")
    if legacy:
        return legacy
    return build_postgres_url(os.environ["POSTGRES_DB"])
