SOURCE_TABLES = (
    "addresses",
    "storage_files",
    "permission_groups",
    "permissions",
    "plans",
    "companies",
    "units",
    "sectors",
    "permission_group_permissions",
    "employees",
    "permission_group_employees",
    "subscriptions",
)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS rpa_outbox (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(150) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    row_pk JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
)
"""

CREATE_WRITE_FN = """
CREATE OR REPLACE FUNCTION aether_rpa_enqueue_write() RETURNS trigger AS $$
BEGIN
    INSERT INTO rpa_outbox (table_name, operation)
    VALUES (TG_TABLE_NAME, lower(TG_OP));
    PERFORM pg_notify('aether_rpa', TG_TABLE_NAME);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql
"""

CREATE_DELETE_FN = """
CREATE OR REPLACE FUNCTION aether_rpa_enqueue_delete() RETURNS trigger AS $$
BEGIN
    INSERT INTO rpa_outbox (table_name, operation, row_pk)
    VALUES (TG_TABLE_NAME, 'delete', to_jsonb(OLD));
    PERFORM pg_notify('aether_rpa', TG_TABLE_NAME);
    RETURN OLD;
END;
$$ LANGUAGE plpgsql
"""


def _trigger_statements(table):
    return [
        f"DROP TRIGGER IF EXISTS aether_rpa_write_{table} ON {table}",
        (
            f"CREATE TRIGGER aether_rpa_write_{table} "
            f"AFTER INSERT OR UPDATE ON {table} "
            f"FOR EACH STATEMENT EXECUTE FUNCTION aether_rpa_enqueue_write()"
        ),
        f"DROP TRIGGER IF EXISTS aether_rpa_delete_{table} ON {table}",
        (
            f"CREATE TRIGGER aether_rpa_delete_{table} "
            f"AFTER DELETE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION aether_rpa_enqueue_delete()"
        ),
    ]


def prepare(connection):
    cursor = connection.cursor()
    cursor.execute(CREATE_TABLE)
    cursor.execute(CREATE_WRITE_FN)
    cursor.execute(CREATE_DELETE_FN)
    for table in SOURCE_TABLES:
        for statement in _trigger_statements(table):
            cursor.execute(statement)
