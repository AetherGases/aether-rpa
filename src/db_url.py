import os
from urllib.parse import quote_plus


def build_postgres_url(dbname: str) -> str:
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
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
    legacy = os.environ.get("DATABASE_A_URL")
    if legacy:
        return legacy
    return build_postgres_url(os.environ["POSTGRES_DB_FIRST_YEAR"])


def resolve_database_b_url(url=None) -> str:
    if url:
        return url
    legacy = os.environ.get("DATABASE_B_URL")
    if legacy:
        return legacy
    return build_postgres_url(os.environ["POSTGRES_DB"])
