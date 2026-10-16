import pytest

from src.db_url import (
    build_postgres_url,
    resolve_database_a_url,
    resolve_database_b_url,
)


def _set_postgres_env(monkeypatch) -> None:
    monkeypatch.setenv("POSTGRES_USER", "app")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss:wrd")
    monkeypatch.setenv("POSTGRES_HOST", "db.example.com")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_SSLMODE", "require")
    monkeypatch.setenv("POSTGRES_DB_FIRST_YEAR", "aether_first")
    monkeypatch.setenv("POSTGRES_DB", "aether_second")


def test_build_postgres_url_encodes_credentials_and_appends_sslmode(monkeypatch) -> None:
    _set_postgres_env(monkeypatch)

    url = build_postgres_url("my_db")

    assert (
        url
        == "postgresql://app:p%40ss%3Awrd@db.example.com:5432/my_db?sslmode=require"
    )


def test_build_postgres_url_defaults_sslmode_to_require(monkeypatch) -> None:
    monkeypatch.setenv("POSTGRES_USER", "u")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.delenv("POSTGRES_SSLMODE", raising=False)

    assert build_postgres_url("db").endswith("?sslmode=require")


def test_resolve_database_a_url_prefers_explicit_argument(monkeypatch) -> None:
    _set_postgres_env(monkeypatch)
    monkeypatch.setenv("DATABASE_A_URL", "postgresql://legacy-a")

    assert resolve_database_a_url("postgresql://explicit") == "postgresql://explicit"


def test_resolve_database_a_url_uses_legacy_env_when_set(monkeypatch) -> None:
    _set_postgres_env(monkeypatch)
    monkeypatch.setenv("DATABASE_A_URL", "postgresql://legacy-a")

    assert resolve_database_a_url() == "postgresql://legacy-a"


def test_resolve_database_a_url_builds_from_postgres_env(monkeypatch) -> None:
    _set_postgres_env(monkeypatch)
    monkeypatch.delenv("DATABASE_A_URL", raising=False)

    assert resolve_database_a_url() == build_postgres_url("aether_first")


def test_resolve_database_b_url_builds_from_postgres_db(monkeypatch) -> None:
    _set_postgres_env(monkeypatch)
    monkeypatch.delenv("DATABASE_B_URL", raising=False)

    assert resolve_database_b_url() == build_postgres_url("aether_second")


def test_resolve_database_b_url_uses_legacy_env_when_set(monkeypatch) -> None:
    _set_postgres_env(monkeypatch)
    monkeypatch.setenv("DATABASE_B_URL", "postgresql://legacy-b")

    assert resolve_database_b_url() == "postgresql://legacy-b"


def test_build_postgres_url_requires_core_env(monkeypatch) -> None:
    monkeypatch.delenv("POSTGRES_USER", raising=False)

    with pytest.raises(KeyError):
        build_postgres_url("db")
