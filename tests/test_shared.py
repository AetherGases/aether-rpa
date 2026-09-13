from dataclasses import dataclass

from shared.extractor import extract
from tests.fake_db import fake_connection


@dataclass
class _Register:
    id: int
    name: str


@dataclass
class _Table:
    registers: list[_Register]


QUERY = "SELECT id, name FROM items"


def test_extract_executes_query_and_fills_table() -> None:
    connection, cursor = fake_connection(["id", "name"], [(1, "alpha")])

    table = extract(connection, QUERY, _Register, _Table)

    cursor.execute.assert_called_once_with(QUERY)
    assert table == _Table(registers=[_Register(id=1, name="alpha")])


def test_extract_empty_rows_returns_empty_table() -> None:
    connection, _cursor = fake_connection(["id", "name"], [])

    table = extract(connection, QUERY, _Register, _Table)

    assert table == _Table(registers=[])
