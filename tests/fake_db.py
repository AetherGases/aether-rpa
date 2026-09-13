from unittest.mock import MagicMock


def fake_connection(columns: list[str], rows: list[tuple]):
    cursor = MagicMock()
    cursor.description = [(name,) for name in columns]
    cursor.fetchall.return_value = rows
    connection = MagicMock()
    connection.cursor.return_value = cursor
    return connection, cursor
