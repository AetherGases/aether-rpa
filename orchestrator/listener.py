from .outbox import drain

CHANNEL = "aether_rpa"
LISTEN_SQL = "LISTEN aether_rpa"


def listen_once(connection_a, connection_b):
    cursor = connection_a.cursor()
    cursor.execute(LISTEN_SQL)
    notifies = getattr(connection_a, "notifies", None)
    if not notifies:
        return
    drain(connection_a, connection_b)
    notifies.clear()
