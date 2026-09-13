# Outbox + LISTEN/NOTIFY Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Worker em `cmd/worker` abre as conexões, garante a tabela de eventos e os triggers no banco A, escuta `NOTIFY` e transfere **uma tabela por vez** para o banco B com `insert`, `update` e `delete`.

**Architecture:** `cmd/worker/prepare.py` cria `rpa_outbox` e triggers se não existirem. Triggers de `INSERT`/`UPDATE` são `FOR EACH STATEMENT` (extract ainda é tabela cheia). Trigger de `DELETE` é `FOR EACH ROW` e grava a PK em `row_pk` (JSONB), porque apagar no B as linhas que **ainda existem** no A estaria errado. `cmd/worker/main.py` cria `connection_a` e `connection_b` e injeta em `prepare` + `listen_once`. Drain chama `drive_to_b` para insert/update e `delete_rows` no destino B para delete. Sem trigger no banco B.

**Tech Stack:** Python 3.11/3.12, pytest, DB-API, PostgreSQL `LISTEN`/`NOTIFY` + `plpgsql`. Factory real de conexão: `psycopg2.connect` (injetável nos testes).

## Global Constraints

- TDD obrigatório; DoD = `pytest tests/ -v --cov --cov-report=term-missing` com 100% e tudo verde.
- Schema do banco A muda (`rpa_outbox` + função + triggers). `prepare.py` aplica isso em runtime se faltar. Documentar em `DATABASE_A_STRUCTURE.md`.
- Não commitar nem dar push sem autorização explícita do usuário.
- `shared.drive` aceita `"insert"` | `"update"` | `"delete"`. Qualquer outro valor levanta `ValueError`.
- Extractores dos 12 pacotes **não** mudam (continuam `SELECT` cheio). Delete **não** passa pelo extract.
- Segurança fora de escopo.
- Windows/OneDrive: mesmo `pytest` da suite atual.

## Decisões propostas (revise e marque o que muda)

1. **Direção v1 = só A → B.** Outbox e triggers só no A. Worker só escreve B.
2. **INSERT/UPDATE:** trigger `FOR EACH STATEMENT`; drain chama `drive_to_b` (extract cheio).
3. **DELETE:** trigger `FOR EACH ROW` + coluna `row_pk`; drain chama `delete_rows` no **banco B** com PKs mapeadas A→B.
4. **Coalesce:** insert/update da mesma tabela viram uma chamada (última `operation` insert-or-update). Deletes **não** coalescem com insert/update: todos os `row_pk` pendentes da tabela são apagados no B, numa chamada `executemany`.
5. **Ordem:** insert/update na ordem de FK (pais → filhos). Delete na ordem inversa (filhos → pais).
6. **Tabela desconhecida:** marca processado, não chama driver.
7. **`main.py` commita** A e B depois de `prepare` e depois de cada `listen_once`.
8. **DSN:** `DATABASE_A_URL` e `DATABASE_B_URL`. Factories `connect_a` / `connect_b` injetáveis.
9. **Limitação insert/update:** extract cheio ainda pode violar UNIQUE no B após o primeiro sync. Fora deste plano: extract por PK / UPSERT.

---

## File structure

- Modify: `shared/driver.py` — aceitar `delete`; adicionar `delete_rows`.
- Modify: `tests/test_shared.py` — delete e operação inválida (`"merge"`).
- Create: `orchestrator/registry.py` — `TABLE_DRIVERS`, `TABLE_ORDER`, `TABLE_DEST`.
- Create: `orchestrator/outbox.py` — fetch/mark/drain (insert, update, delete).
- Create: `orchestrator/listener.py` — `listen_once`.
- Create: `orchestrator/__init__.py`
- Create: `cmd/__init__.py` (vazio)
- Create: `cmd/worker/__init__.py` (vazio)
- Create: `cmd/worker/prepare.py` — DDL idempotente no banco A.
- Create: `cmd/worker/main.py` — cria conexões, injeta, prepare + listen + commit.
- Create: `tests/test_orchestrator.py`
- Create: `tests/test_worker.py`
- Modify: `tests/test_packages.py` — não precisa importar `cmd`.
- Modify: `requirements.txt` — `psycopg2-binary>=2.9,<3`
- Modify: `DATABASE_A_STRUCTURE.md`
- Modify: `AGENT_NOTES/architecture.md`
- Do not modify: `*/extractor.py`, `*/transformer.py`, os 12 `*/driver.py` (já encaminham `operation`).

`TABLE_DEST` (tabela A → tabela B, PK A, PK B):

| A | B | PK A | PK B |
|---|---|---|---|
| `addresses` | `address` | `id` | `id` |
| `companies` | `enterprise` | `id` | `id` |
| `units` | `unit` | `id` | `id` |
| `sectors` | `department` | `id` | `id` |
| `storage_files` | `storage_file` | `id` | `id` |
| `permission_groups` | `permission_group` | `id` | `id` |
| `permissions` | `permission` | `id` | `id` |
| `permission_group_permissions` | `permission_group_permission` | `id` | `id` |
| `employees` | `employee` | `id` | `id` |
| `permission_group_employees` | `permission_group_employee` | `employee_id`, `permission_group_id` | `id_employee`, `id_permission_group` |
| `plans` | `plan` | `id` | `id` |
| `subscriptions` | `plan_subscription` | `id` | `id` |

---

### Task 1: `shared.drive` com `delete`

**Files:**
- Modify: `shared/driver.py`
- Modify: `tests/test_shared.py`

**Interfaces:**
- Consumes: `table.registers`, `pk_fields`
- Produces:
  - `drive(connection, table, operation, table_name, pk_fields)` com `operation in {"insert", "update", "delete"}`
  - `delete_rows(connection, table_name, pk_fields, pk_values)` onde `pk_values` é `list[tuple]`

`delete` em `drive`: `DELETE FROM {table} WHERE pk = %s` via `executemany`, só colunas de PK. Tabela só-PK (`permission_group_employee`) **executa** o DELETE (diferente do UPDATE no-op).

- [ ] **Step 1: Write the failing tests**

Em `tests/test_shared.py`, **trocar** `test_drive_rejects_unknown_operation` para usar `"merge"` e **acrescentar**:

```python
from shared.driver import delete_rows, drive


def test_drive_delete_uses_pk_where() -> None:
    connection, cursor = fake_connection(["id", "name"], [])
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])

    drive(connection, table, "delete", "items", ("id",))

    cursor.executemany.assert_called_once_with(
        "DELETE FROM items WHERE id = %s",
        [(1,)],
    )


def test_drive_delete_composite_pk() -> None:
    connection, cursor = fake_connection(["employee_id", "permission_group_id"], [])
    table = _PkOnlyTable(
        registers=[_PkOnlyRegister(employee_id=1, permission_group_id=2)]
    )

    drive(
        connection,
        table,
        "delete",
        "permission_group_employees",
        ("employee_id", "permission_group_id"),
    )

    cursor.executemany.assert_called_once_with(
        "DELETE FROM permission_group_employees WHERE employee_id = %s AND permission_group_id = %s",
        [(1, 2)],
    )


def test_delete_rows_executemany() -> None:
    connection, cursor = fake_connection([], [])

    delete_rows(connection, "address", ("id",), [(1,), (2,)])

    cursor.executemany.assert_called_once_with(
        "DELETE FROM address WHERE id = %s",
        [(1,), (2,)],
    )


def test_delete_rows_empty_does_not_execute() -> None:
    connection, cursor = fake_connection([], [])

    delete_rows(connection, "address", ("id",), [])

    cursor.executemany.assert_not_called()
    connection.cursor.assert_not_called()


def test_drive_rejects_unknown_operation() -> None:
    connection, _cursor = fake_connection(["id", "name"], [])
    table = _DriveTable(registers=[_DriveRegister(id=1, name="alpha")])

    with pytest.raises(ValueError):
        drive(connection, table, "merge", "items", ("id",))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_shared.py -v`

Expected: FAIL — `delete` ainda levanta `ValueError`; `delete_rows` não existe.

- [ ] **Step 3: Write minimal implementation**

Substituir `shared/driver.py` por:

```python
from dataclasses import fields
from enum import Enum


def drive(connection, table, operation, table_name, pk_fields):
    if operation not in ("insert", "update", "delete"):
        raise ValueError(operation)
    registers = table.registers
    if not registers:
        return
    columns = [field.name for field in fields(registers[0])]
    pk = list(pk_fields)
    if operation == "delete":
        pk_values = [
            tuple(_bind(getattr(register, column)) for column in pk)
            for register in registers
        ]
        delete_rows(connection, table_name, pk, pk_values)
        return
    if operation == "update":
        set_columns = [column for column in columns if column not in pk]
        if not set_columns:
            return
        set_sql = ", ".join(f"{column} = %s" for column in set_columns)
        where_sql = " AND ".join(f"{column} = %s" for column in pk)
        query = f"UPDATE {table_name} SET {set_sql} WHERE {where_sql}"
        bind_columns = set_columns + pk
    else:
        col_sql = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO {table_name} ({col_sql}) VALUES ({placeholders})"
        bind_columns = columns
    rows = [
        tuple(_bind(getattr(register, column)) for column in bind_columns)
        for register in registers
    ]
    cursor = connection.cursor()
    cursor.executemany(query, rows)


def delete_rows(connection, table_name, pk_fields, pk_values):
    if not pk_values:
        return
    pk = list(pk_fields)
    where_sql = " AND ".join(f"{column} = %s" for column in pk)
    query = f"DELETE FROM {table_name} WHERE {where_sql}"
    cursor = connection.cursor()
    cursor.executemany(query, list(pk_values))


def _bind(value):
    if isinstance(value, Enum):
        return value.value
    return value
```

Exportar `delete_rows` em `shared/__init__.py`:

```python
from .driver import delete_rows, drive
from .extractor import extract
from .transformer import transform

__all__ = ["delete_rows", "drive", "extract", "transform"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_shared.py -v`

Expected: PASS

- [ ] **Step 5: Commit** — só se o usuário autorizar. Mensagem: `shared.drive deletes by primary key`

---

### Task 2: Registry tabela A → driver e destino B

**Files:**
- Create: `orchestrator/registry.py`
- Create: `orchestrator/__init__.py`
- Test: `tests/test_orchestrator.py`

**Interfaces:**
- Produces: `TABLE_DRIVERS`, `TABLE_ORDER`, `TABLE_DEST`
- `TABLE_DEST[table_a] = (table_b, pk_a: tuple[str, ...], pk_b: tuple[str, ...])`

- [ ] **Step 1: Write the failing tests**

```python
from orchestrator.registry import TABLE_DEST, TABLE_DRIVERS, TABLE_ORDER


def test_table_drivers_maps_all_database_a_tables() -> None:
    from address.driver import drive_to_b as address_to_b
    from department.driver import drive_to_b as department_to_b
    from employee.driver import drive_to_b as employee_to_b
    from enterprise.driver import drive_to_b as enterprise_to_b
    from permission.driver import drive_to_b as permission_to_b
    from permission_group.driver import drive_to_b as permission_group_to_b
    from permission_group_employee.driver import drive_to_b as pge_to_b
    from permission_group_permission.driver import drive_to_b as pgp_to_b
    from plan.driver import drive_to_b as plan_to_b
    from plan_subscription.driver import drive_to_b as plan_subscription_to_b
    from storage_file.driver import drive_to_b as storage_file_to_b
    from unit.driver import drive_to_b as unit_to_b

    assert TABLE_DRIVERS == {
        "addresses": address_to_b,
        "companies": enterprise_to_b,
        "units": unit_to_b,
        "sectors": department_to_b,
        "storage_files": storage_file_to_b,
        "permission_groups": permission_group_to_b,
        "permissions": permission_to_b,
        "permission_group_permissions": pgp_to_b,
        "employees": employee_to_b,
        "permission_group_employees": pge_to_b,
        "plans": plan_to_b,
        "subscriptions": plan_subscription_to_b,
    }


def test_table_order_lists_parents_before_children() -> None:
    assert TABLE_ORDER == [
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
    ]
    assert set(TABLE_ORDER) == set(TABLE_DRIVERS) == set(TABLE_DEST)


def test_table_dest_maps_b_names_and_pks() -> None:
    assert TABLE_DEST["companies"] == ("enterprise", ("id",), ("id",))
    assert TABLE_DEST["permission_group_employees"] == (
        "permission_group_employee",
        ("employee_id", "permission_group_id"),
        ("id_employee", "id_permission_group"),
    )
    assert TABLE_DEST["subscriptions"] == (
        "plan_subscription",
        ("id",),
        ("id",),
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_orchestrator.py -v`

Expected: FAIL `No module named 'orchestrator'`

- [ ] **Step 3: Write minimal implementation**

`orchestrator/registry.py`:

```python
from address.driver import drive_to_b as address_to_b
from department.driver import drive_to_b as department_to_b
from employee.driver import drive_to_b as employee_to_b
from enterprise.driver import drive_to_b as enterprise_to_b
from permission.driver import drive_to_b as permission_to_b
from permission_group.driver import drive_to_b as permission_group_to_b
from permission_group_employee.driver import drive_to_b as pge_to_b
from permission_group_permission.driver import drive_to_b as pgp_to_b
from plan.driver import drive_to_b as plan_to_b
from plan_subscription.driver import drive_to_b as plan_subscription_to_b
from storage_file.driver import drive_to_b as storage_file_to_b
from unit.driver import drive_to_b as unit_to_b

TABLE_DRIVERS = {
    "addresses": address_to_b,
    "companies": enterprise_to_b,
    "units": unit_to_b,
    "sectors": department_to_b,
    "storage_files": storage_file_to_b,
    "permission_groups": permission_group_to_b,
    "permissions": permission_to_b,
    "permission_group_permissions": pgp_to_b,
    "employees": employee_to_b,
    "permission_group_employees": pge_to_b,
    "plans": plan_to_b,
    "subscriptions": plan_subscription_to_b,
}

TABLE_ORDER = [
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
]

TABLE_DEST = {
    "addresses": ("address", ("id",), ("id",)),
    "companies": ("enterprise", ("id",), ("id",)),
    "units": ("unit", ("id",), ("id",)),
    "sectors": ("department", ("id",), ("id",)),
    "storage_files": ("storage_file", ("id",), ("id",)),
    "permission_groups": ("permission_group", ("id",), ("id",)),
    "permissions": ("permission", ("id",), ("id",)),
    "permission_group_permissions": ("permission_group_permission", ("id",), ("id",)),
    "employees": ("employee", ("id",), ("id",)),
    "permission_group_employees": (
        "permission_group_employee",
        ("employee_id", "permission_group_id"),
        ("id_employee", "id_permission_group"),
    ),
    "plans": ("plan", ("id",), ("id",)),
    "subscriptions": ("plan_subscription", ("id",), ("id",)),
}
```

`orchestrator/__init__.py`:

```python
from .registry import TABLE_DEST, TABLE_DRIVERS, TABLE_ORDER

__all__ = ["TABLE_DEST", "TABLE_DRIVERS", "TABLE_ORDER"]
```

- [ ] **Step 4: Run tests** — Expected: PASS

- [ ] **Step 5: Commit** — se autorizado. Mensagem: `orchestrator registry maps A tables to B destinations`

---

### Task 3: Drain com insert, update e delete

**Files:**
- Create: `orchestrator/outbox.py`
- Modify: `orchestrator/__init__.py`
- Modify: `tests/test_orchestrator.py`

**Interfaces:**
- `FETCH_PENDING = "SELECT id, table_name, operation, row_pk FROM rpa_outbox WHERE processed_at IS NULL ORDER BY id"`
- `MARK_PROCESSED = "UPDATE rpa_outbox SET processed_at = CURRENT_TIMESTAMP WHERE id = ANY(%s)"`
- `fetch_pending(connection) -> list[tuple]`  # `(id, table_name, operation, row_pk)`
- `mark_processed(connection, ids) -> None`
- `drain(connection_a, connection_b) -> None`

Regras do `drain`:

1. Buscar pendentes. Vazio → return.
2. Separar linhas `operation == "delete"` das demais.
3. Insert/update: agrupar por `table_name`, última operation ganha; percorrer `TABLE_ORDER`; se driver existe, `TABLE_DRIVERS[table](connection_a, connection_b, operation)`.
4. Delete: agrupar `row_pk` por `table_name`; percorrer `reversed(TABLE_ORDER)`; para cada tabela em `TABLE_DEST`, montar lista de tuplas PK B (`row_pk[pk_a]` na ordem `pk_b`) e chamar `delete_rows(connection_b, table_b, pk_b, values)`. `row_pk` chega como `dict` (jsonb do psycopg). Se vier `str`, `json.loads`.
5. Tabela fora do registry: não chama nada.
6. `mark_processed` com **todos** os ids lidos.

- [ ] **Step 1: Write the failing tests**

```python
from orchestrator.outbox import FETCH_PENDING, MARK_PROCESSED, drain, fetch_pending, mark_processed
from tests.fake_db import fake_connection


def test_fetch_pending_includes_row_pk() -> None:
    connection, cursor = fake_connection(
        ["id", "table_name", "operation", "row_pk"],
        [(1, "companies", "insert", None)],
    )
    rows = fetch_pending(connection)
    cursor.execute.assert_called_once_with(FETCH_PENDING)
    assert rows == [(1, "companies", "insert", None)]


def test_mark_processed_updates_ids() -> None:
    connection, cursor = fake_connection([], [])
    mark_processed(connection, [1, 2])
    cursor.execute.assert_called_once_with(MARK_PROCESSED, ([1, 2],))


def test_mark_processed_empty_ids_does_not_execute() -> None:
    connection, cursor = fake_connection([], [])
    mark_processed(connection, [])
    cursor.execute.assert_not_called()
    connection.cursor.assert_not_called()


def test_drain_insert_update_last_operation_wins(monkeypatch) -> None:
    connection_a, cursor_a = fake_connection(
        ["id", "table_name", "operation", "row_pk"],
        [
            (1, "companies", "insert", None),
            (2, "companies", "update", None),
            (3, "addresses", "insert", None),
        ],
    )
    connection_b, _cursor_b = fake_connection([], [])
    calls = []
    monkeypatch.setattr(
        "orchestrator.outbox.TABLE_DRIVERS",
        {
            "addresses": lambda a, b, op: calls.append(("addresses", op)),
            "companies": lambda a, b, op: calls.append(("companies", op)),
        },
    )
    monkeypatch.setattr(
        "orchestrator.outbox.TABLE_ORDER",
        ["addresses", "companies"],
    )
    monkeypatch.setattr("orchestrator.outbox.TABLE_DEST", {})

    drain(connection_a, connection_b)

    assert calls == [("addresses", "insert"), ("companies", "update")]
    assert cursor_a.execute.call_args_list[-1].args == (MARK_PROCESSED, ([1, 2, 3],))


def test_drain_delete_maps_pk_and_deletes_on_b(monkeypatch) -> None:
    connection_a, cursor_a = fake_connection(
        ["id", "table_name", "operation", "row_pk"],
        [
            (1, "companies", "delete", {"id": 9}),
            (2, "permission_group_employees", "delete", {
                "employee_id": 1,
                "permission_group_id": 2,
            }),
        ],
    )
    connection_b, _cursor_b = fake_connection([], [])
    deleted = []
    monkeypatch.setattr(
        "orchestrator.outbox.delete_rows",
        lambda conn, table, pk, values: deleted.append((conn, table, pk, values)),
    )
    monkeypatch.setattr("orchestrator.outbox.TABLE_DRIVERS", {})
    monkeypatch.setattr(
        "orchestrator.outbox.TABLE_ORDER",
        ["companies", "permission_group_employees"],
    )
    monkeypatch.setattr(
        "orchestrator.outbox.TABLE_DEST",
        {
            "companies": ("enterprise", ("id",), ("id",)),
            "permission_group_employees": (
                "permission_group_employee",
                ("employee_id", "permission_group_id"),
                ("id_employee", "id_permission_group"),
            ),
        },
    )

    drain(connection_a, connection_b)

    assert deleted == [
        (
            connection_b,
            "permission_group_employee",
            ("id_employee", "id_permission_group"),
            [(1, 2)],
        ),
        (connection_b, "enterprise", ("id",), [(9,)]),
    ]
    assert cursor_a.execute.call_args_list[-1].args == (MARK_PROCESSED, ([1, 2],))


def test_drain_skips_unknown_table_but_marks_processed(monkeypatch) -> None:
    connection_a, cursor_a = fake_connection(
        ["id", "table_name", "operation", "row_pk"],
        [(1, "not_a_table", "insert", None)],
    )
    connection_b, _cursor_b = fake_connection([], [])
    monkeypatch.setattr("orchestrator.outbox.TABLE_DRIVERS", {})
    monkeypatch.setattr("orchestrator.outbox.TABLE_ORDER", [])
    monkeypatch.setattr("orchestrator.outbox.TABLE_DEST", {})

    drain(connection_a, connection_b)

    assert cursor_a.execute.call_args_list[-1].args == (MARK_PROCESSED, ([1],))


def test_drain_empty_pending_does_not_mark() -> None:
    connection_a, cursor_a = fake_connection(
        ["id", "table_name", "operation", "row_pk"], []
    )
    connection_b, _cursor_b = fake_connection([], [])
    drain(connection_a, connection_b)
    cursor_a.execute.assert_called_once_with(FETCH_PENDING)
```

- [ ] **Step 2: Run tests** — Expected: FAIL import `orchestrator.outbox`

- [ ] **Step 3: Write `orchestrator/outbox.py`**

```python
from shared.driver import delete_rows

from .registry import TABLE_DEST, TABLE_DRIVERS, TABLE_ORDER

FETCH_PENDING = (
    "SELECT id, table_name, operation, row_pk FROM rpa_outbox "
    "WHERE processed_at IS NULL ORDER BY id"
)
MARK_PROCESSED = (
    "UPDATE rpa_outbox SET processed_at = CURRENT_TIMESTAMP WHERE id = ANY(%s)"
)


def fetch_pending(connection):
    cursor = connection.cursor()
    cursor.execute(FETCH_PENDING)
    return cursor.fetchall()


def mark_processed(connection, ids):
    if not ids:
        return
    cursor = connection.cursor()
    cursor.execute(MARK_PROCESSED, (list(ids),))


def _pk_tuple(row_pk, pk_a):
    payload = row_pk
    if isinstance(payload, str):
        import json
        payload = json.loads(payload)
    return tuple(payload[column] for column in pk_a)


def drain(connection_a, connection_b):
    rows = fetch_pending(connection_a)
    if not rows:
        return
    ids = []
    latest_write = {}
    deletes = {}
    for row_id, table_name, operation, row_pk in rows:
        ids.append(row_id)
        if operation == "delete":
            deletes.setdefault(table_name, []).append(row_pk)
        else:
            latest_write[table_name] = operation
    for table_name in TABLE_ORDER:
        operation = latest_write.get(table_name)
        driver = TABLE_DRIVERS.get(table_name)
        if operation is None or driver is None:
            continue
        driver(connection_a, connection_b, operation)
    for table_name in reversed(TABLE_ORDER):
        payloads = deletes.get(table_name)
        dest = TABLE_DEST.get(table_name)
        if not payloads or dest is None:
            continue
        table_b, pk_a, pk_b = dest
        values = [_pk_tuple(row_pk, pk_a) for row_pk in payloads]
        delete_rows(connection_b, table_b, pk_b, values)
    mark_processed(connection_a, ids)
```

Atualizar `orchestrator/__init__.py` para exportar `drain`, `fetch_pending`, `mark_processed`.

- [ ] **Step 4: Run** `pytest tests/test_orchestrator.py -v` — Expected: PASS

- [ ] **Step 5: Commit** — se autorizado.

---

### Task 4: Listener

**Files:**
- Create: `orchestrator/listener.py`
- Modify: `orchestrator/__init__.py`
- Modify: `tests/test_orchestrator.py`

**Interfaces:** `CHANNEL = "aether_rpa"`; `LISTEN_SQL = "LISTEN aether_rpa"`; `listen_once(connection_a, connection_b)` — `LISTEN`; se `connection_a.notifies` truthy, `drain` e `notifies.clear()`.

- [ ] **Step 1: Write the failing tests**

```python
from orchestrator.listener import CHANNEL, LISTEN_SQL, listen_once


def test_listen_once_without_notify_does_not_drain(monkeypatch) -> None:
    connection_a, cursor_a = fake_connection([], [])
    connection_a.notifies = []
    connection_b, _cursor_b = fake_connection([], [])
    drained = []
    monkeypatch.setattr(
        "orchestrator.listener.drain",
        lambda a, b: drained.append((a, b)),
    )
    listen_once(connection_a, connection_b)
    cursor_a.execute.assert_called_once_with(LISTEN_SQL)
    assert drained == []
    assert CHANNEL == "aether_rpa"


def test_listen_once_with_notify_drains_and_clears(monkeypatch) -> None:
    connection_a, cursor_a = fake_connection([], [])
    connection_a.notifies = [object()]
    connection_b, _cursor_b = fake_connection([], [])
    drained = []
    monkeypatch.setattr(
        "orchestrator.listener.drain",
        lambda a, b: drained.append((a, b)),
    )
    listen_once(connection_a, connection_b)
    assert drained == [(connection_a, connection_b)]
    assert connection_a.notifies == []
```

- [ ] **Step 2–4:** RED, implementar igual ao plano anterior (`listen_once` + `drain`), GREEN.

`orchestrator/listener.py`:

```python
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
```

- [ ] **Step 5: Commit** — se autorizado.

---

### Task 5: `cmd/worker/prepare.py`

**Files:**
- Create: `cmd/__init__.py` (vazio)
- Create: `cmd/worker/__init__.py` (vazio)
- Create: `cmd/worker/prepare.py`
- Test: `tests/test_worker.py`

**Interfaces:**
- `EVENT_TABLE = "rpa_outbox"`
- `SOURCE_TABLES: tuple[str, ...]` — as 12 tabelas A, mesma ordem de `TABLE_ORDER`
- `prepare(connection_a) -> None` — executa DDL idempotente **só no banco A**

DDL (nessa ordem):

1. `CREATE TABLE IF NOT EXISTS rpa_outbox (id SERIAL PRIMARY KEY, table_name VARCHAR(150) NOT NULL, operation VARCHAR(10) NOT NULL, row_pk JSONB, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, processed_at TIMESTAMP)`
2. `CREATE OR REPLACE FUNCTION aether_rpa_enqueue_write() RETURNS trigger` — `INSERT INTO rpa_outbox (table_name, operation) VALUES (TG_TABLE_NAME, lower(TG_OP)); PERFORM pg_notify('aether_rpa', TG_TABLE_NAME); RETURN NULL;`
3. `CREATE OR REPLACE FUNCTION aether_rpa_enqueue_delete() RETURNS trigger` — `INSERT INTO rpa_outbox (table_name, operation, row_pk) VALUES (TG_TABLE_NAME, 'delete', to_jsonb(OLD)); PERFORM pg_notify('aether_rpa', TG_TABLE_NAME); RETURN OLD;`
4. Para cada tabela em `SOURCE_TABLES`:
   - `DROP TRIGGER IF EXISTS aether_rpa_write_{table} ON {table}`
   - `CREATE TRIGGER aether_rpa_write_{table} AFTER INSERT OR UPDATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION aether_rpa_enqueue_write();`
   - `DROP TRIGGER IF EXISTS aether_rpa_delete_{table} ON {table}`
   - `CREATE TRIGGER aether_rpa_delete_{table} AFTER DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION aether_rpa_enqueue_delete();`

Se o Postgres A for &lt; 14, `EXECUTE FUNCTION` vira `EXECUTE PROCEDURE` na revisão — default deste plano: `EXECUTE FUNCTION`.

- [ ] **Step 1: Write the failing tests**

```python
from cmd.worker.prepare import SOURCE_TABLES, prepare
from tests.fake_db import fake_connection


def test_prepare_creates_event_table_functions_and_triggers() -> None:
    connection, cursor = fake_connection([], [])

    prepare(connection)

    scripts = [call.args[0] for call in cursor.execute.call_args_list]
    joined = "\n".join(scripts)
    assert "CREATE TABLE IF NOT EXISTS rpa_outbox" in joined
    assert "row_pk JSONB" in joined
    assert "aether_rpa_enqueue_write" in joined
    assert "aether_rpa_enqueue_delete" in joined
    assert "to_jsonb(OLD)" in joined
    assert "pg_notify('aether_rpa'" in joined
    for table in SOURCE_TABLES:
        assert f"ON {table}" in joined
        assert f"aether_rpa_write_{table}" in joined
        assert f"aether_rpa_delete_{table}" in joined
    assert "AFTER INSERT OR UPDATE" in joined
    assert "AFTER DELETE" in joined
    assert SOURCE_TABLES == (
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


def test_prepare_is_safe_to_run_twice() -> None:
    connection, cursor = fake_connection([], [])
    prepare(connection)
    first = cursor.execute.call_count
    prepare(connection)
    assert cursor.execute.call_count == first * 2
```

- [ ] **Step 2: Run** `pytest tests/test_worker.py -v` — Expected: FAIL import

- [ ] **Step 3: Write `cmd/worker/prepare.py`**

```python
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
```

- [ ] **Step 4:** GREEN `pytest tests/test_worker.py -v`

- [ ] **Step 5: Commit** — se autorizado.

---

### Task 6: `cmd/worker/main.py` com injeção de conexões

**Files:**
- Create: `cmd/worker/main.py`
- Modify: `tests/test_worker.py`
- Modify: `requirements.txt` (acrescentar `psycopg2-binary>=2.9,<3`)

**Interfaces:**

```python
def connect_a(url=None):
    # psycopg2.connect(url or os.environ["DATABASE_A_URL"])

def connect_b(url=None):
    # psycopg2.connect(url or os.environ["DATABASE_B_URL"])

def run(connection_a, connection_b, prepare_fn, listen_fn):
    prepare_fn(connection_a)
    connection_a.commit()
    listen_fn(connection_a, connection_b)
    connection_a.commit()
    connection_b.commit()

def main(connect_a_fn=connect_a, connect_b_fn=connect_b, prepare_fn=prepare, listen_fn=listen_once):
    connection_a = connect_a_fn()
    connection_b = connect_b_fn()
    run(connection_a, connection_b, prepare_fn, listen_fn)
```

`connect_a` / `connect_b` só importam `psycopg2` dentro da função (testes que injetam factories não carregam o driver).

- [ ] **Step 1: Write the failing tests**

```python
from unittest.mock import MagicMock

from cmd.worker.main import main, run


def test_run_injects_connections_into_prepare_and_listen() -> None:
    connection_a = MagicMock()
    connection_b = MagicMock()
    prepared = []
    listened = []

    run(
        connection_a,
        connection_b,
        prepare_fn=lambda conn: prepared.append(conn),
        listen_fn=lambda a, b: listened.append((a, b)),
    )

    assert prepared == [connection_a]
    assert listened == [(connection_a, connection_b)]
    assert connection_a.commit.call_count == 2
    connection_b.commit.assert_called_once_with()


def test_main_creates_connections_and_injects_them() -> None:
    connection_a = MagicMock(name="a")
    connection_b = MagicMock(name="b")
    prepared = []
    listened = []

    main(
        connect_a_fn=lambda: connection_a,
        connect_b_fn=lambda: connection_b,
        prepare_fn=lambda conn: prepared.append(conn),
        listen_fn=lambda a, b: listened.append((a, b)),
    )

    assert prepared == [connection_a]
    assert listened == [(connection_a, connection_b)]
```

- [ ] **Step 2:** RED — `cmd.worker.main` inexistente

- [ ] **Step 3: Write `cmd/worker/main.py`**

```python
import os

from cmd.worker.prepare import prepare
from orchestrator.listener import listen_once


def connect_a(url=None):
    import psycopg2
    return psycopg2.connect(url or os.environ["DATABASE_A_URL"])


def connect_b(url=None):
    import psycopg2
    return psycopg2.connect(url or os.environ["DATABASE_B_URL"])


def run(connection_a, connection_b, prepare_fn, listen_fn):
    prepare_fn(connection_a)
    connection_a.commit()
    listen_fn(connection_a, connection_b)
    connection_a.commit()
    connection_b.commit()


def main(
    connect_a_fn=connect_a,
    connect_b_fn=connect_b,
    prepare_fn=prepare,
    listen_fn=listen_once,
):
    connection_a = connect_a_fn()
    connection_b = connect_b_fn()
    run(connection_a, connection_b, prepare_fn, listen_fn)


if __name__ == "__main__":
    main()
```

`requirements.txt` fica:

```
pytest>=8.0,<9
pytest-cov>=5.0,<6
psycopg2-binary>=2.9,<3
```

- [ ] **Step 4:** `pytest tests/test_worker.py tests/test_orchestrator.py tests/test_shared.py -v` — PASS

- [ ] **Step 5: Commit** — se autorizado.

---

### Task 7: Documentação do banco A

**Files:**
- Modify: `DATABASE_A_STRUCTURE.md`
- Modify: `AGENT_NOTES/architecture.md`

Acrescentar seção:

```markdown
# RPA

## `rpa_outbox`

| Campo          | Tipo           | Restrições                  |
| -------------- | -------------- | --------------------------- |
| `id`           | `SERIAL`       | PK                          |
| `table_name`   | `VARCHAR(150)` | NOT NULL                    |
| `operation`    | `VARCHAR(10)`  | NOT NULL                    |
| `row_pk`       | `JSONB`        | (preenchido só em DELETE)   |
| `created_at`   | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |
| `processed_at` | `TIMESTAMP`    |                             |

`cmd/worker/prepare.py` cria a tabela e os triggers se não existirem. `INSERT`/`UPDATE`: `FOR EACH STATEMENT`. `DELETE`: `FOR EACH ROW` com `row_pk`. Canal `aether_rpa`. Só banco A.
```

`AGENT_NOTES/architecture.md`:

```
Pacotes na raiz = tabelas do banco B. definition/extractor/transformer/driver: extract origem, INSERT/UPDATE/DELETE destino.
orchestrator drena rpa_outbox no A e chama drive_to_b ou delete_rows no B.
cmd/worker/main.py injeta conexões; prepare.py cria outbox+triggers se faltarem.
```

- [ ] **Step 1:** Não há teste de markdown. Aplicar os dois arquivos.
- [ ] **Step 2:** `pytest tests/ -v --cov --cov-report=term-missing` — 100%, tudo verde.
- [ ] **Step 3: Commit** — se autorizado.

---

### Task 8: Cobertura da suite

- [ ] **Step 1:** `pytest tests/ -v --cov --cov-report=term-missing`

Expected: TOTAL 100%. Se `json.loads` em `_pk_tuple` ficar sem cobertura, acrescentar um caso de `row_pk` string `'{"id": 1}'` em `test_drain_delete_maps_pk_and_deletes_on_b` **ou** remover o ramo `str` e exigir dict (YAGNI: remover `json.loads` se os testes só passam dict).

- [ ] **Step 2: Commit** — se autorizado.

---

## Fora deste plano

- Extract por PK / UPSERT no insert/update.
- Triggers no banco B / `drive_to_a` orquestrado.
- Loop `while True` + `select` (um ciclo `listen_once` por execução de `main`; operador pode relançar ou embrulhar depois).
- Aplicar DDL no Postgres à mão (o worker faz via `prepare`).

## Como ligar (depois de aplicar o código)

```
set DATABASE_A_URL=postgresql://...
set DATABASE_B_URL=postgresql://...
python -m cmd.worker.main
```

(`python -m cmd.worker.main` usa o `if __name__ == "__main__"` da Task 6.)
