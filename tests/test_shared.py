from dataclasses import dataclass

from shared.extractor import extract
from shared.transformer import transform
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


@dataclass
class _RegisterA:
    id: int
    name: str
    address_id: int | None


@dataclass
class _TableA:
    registers: list[_RegisterA]


@dataclass
class _RegisterB:
    id: int
    name: str
    id_address: int | None


@dataclass
class _TableB:
    registers: list[_RegisterB]


_FIELD_MAP = {"address_id": "id_address"}


def test_transform_remaps_named_fields_and_copies_the_rest() -> None:
    table = _TableA(registers=[_RegisterA(id=1, name="alpha", address_id=10)])

    result = transform(table, _RegisterB, _TableB, _FIELD_MAP)

    assert result == _TableB(registers=[_RegisterB(id=1, name="alpha", id_address=10)])


def test_transform_empty_registers_returns_empty_table() -> None:
    result = transform(_TableA(registers=[]), _RegisterB, _TableB, _FIELD_MAP)

    assert result == _TableB(registers=[])


def test_transform_applies_inverse_field_map() -> None:
    inverse = {target: source for source, target in _FIELD_MAP.items()}
    table = _TableB(registers=[_RegisterB(id=1, name="alpha", id_address=10)])

    result = transform(table, _RegisterA, _TableA, inverse)

    assert result == _TableA(registers=[_RegisterA(id=1, name="alpha", address_id=10)])
