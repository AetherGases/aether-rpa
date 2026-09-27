# Modelo de Dados

Artefato de origem: `new_first_year_database.sql`. Tabelas abaixo cobrem o contrato RPA (11 tabelas). Colunas extras só de A (ex.: `country`, `email`, `currency`, `is_active`) permanecem no SQL mas ficam fora do mapeamento de replicação.

## Enums

### `status_employee`

| Valor          |
| -------------- |
| `active`       |
| `on leave`     |
| `on vacation`  |
| `dismissed`    |

# Referências

## `addresses`

| Campo          | Tipo           | Restrições                  |
| -------------- | -------------- | --------------------------- |
| `id`           | `SERIAL`       | PK                          |
| `zip_code`     | `CHAR(8)`      |                             |
| `street`       | `VARCHAR(255)` | NOT NULL                    |
| `number`       | `VARCHAR(20)`  | NOT NULL                    |
| `complement`   | `VARCHAR(100)` |                             |
| `city`         | `VARCHAR(100)` | NOT NULL                    |
| `neighborhood` | `VARCHAR(150)` | NOT NULL                    |
| `state`        | `VARCHAR(100)` | NOT NULL                    |
| `country`      | `VARCHAR(100)` | (só A)                      |
| `is_active`    | `BOOLEAN`      | DEFAULT `TRUE` (só A)       |
| `created_at`   | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at`   | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |

## `companies`

| Campo               | Tipo           | Restrições                  |
| ------------------- | -------------- | --------------------------- |
| `id`                | `SERIAL`       | PK                          |
| `name`              | `VARCHAR(255)` | NOT NULL                    |
| `trade_name`        | `VARCHAR(150)` |                             |
| `cnpj`              | `CHAR(14)`     | NOT NULL, UNIQUE            |
| `size`              | `INTEGER`      | CHECK `size > 0` (só A)     |
| `registration_date` | `DATE`         | (só A)                      |
| `tax_id`            | `VARCHAR(50)`  | (só A)                      |
| `email`             | `VARCHAR(255)` | (só A)                      |
| `address_id`        | `INTEGER`      | FK → `addresses.id`         |
| `is_active`         | `BOOLEAN`      | DEFAULT `TRUE` (só A)       |
| `created_at`        | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at`        | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |

## `units`

| Campo        | Tipo           | Restrições                  |
| ------------ | -------------- | --------------------------- |
| `id`         | `SERIAL`       | PK                          |
| `name`       | `VARCHAR(255)` | (só A)                      |
| `company_id` | `INTEGER`      | FK → `companies.id`         |
| `address_id` | `INTEGER`      | FK → `addresses.id`         |
| `cnpj`       | `VARCHAR(50)`  | NOT NULL                    |
| `cnae`       | `VARCHAR(50)`  |                             |
| `is_active`  | `BOOLEAN`      | DEFAULT `TRUE` (só A)       |
| `created_at` | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |

## `sectors`

| Campo         | Tipo           | Restrições                  |
| ------------- | -------------- | --------------------------- |
| `id`          | `SERIAL`       | PK                          |
| `name`        | `VARCHAR(150)` | NOT NULL                    |
| `description` | `VARCHAR(255)` |                             |
| `unit_id`     | `INTEGER`      | FK → `units.id`             |
| `company_id`  | `INTEGER`      | FK → `companies.id`         |
| `is_active`   | `BOOLEAN`      | DEFAULT `TRUE` (só A)       |
| `created_at`  | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at`  | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |

# Employees

## `storage_files`

| Campo        | Tipo           | Restrições                  |
| ------------ | -------------- | --------------------------- |
| `id`         | `SERIAL`       | PK                          |
| `name`       | `VARCHAR(150)` | NOT NULL                    |
| `path`       | `VARCHAR(255)` | NOT NULL                    |
| `created_at` | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |

## `permission_groups`

| Campo        | Tipo           | Restrições                  |
| ------------ | -------------- | --------------------------- |
| `id`         | `SERIAL`       | PK                          |
| `name`       | `VARCHAR(100)` | NOT NULL                    |
| `company_id` | `INTEGER`      | FK → `companies.id`         |
| `is_active`  | `BOOLEAN`      | DEFAULT `TRUE` (só A)       |
| `created_at` | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |

## `permissions`

| Campo         | Tipo           | Restrições                  |
| ------------- | -------------- | --------------------------- |
| `id`          | `SERIAL`       | PK                          |
| `name`        | `VARCHAR(100)` | NOT NULL                    |
| `description` | `VARCHAR(255)` |                             |
| `url`         | `VARCHAR(50)`  | NOT NULL                    |
| `is_active`   | `BOOLEAN`      | DEFAULT `TRUE` (só A)       |
| `created_at`  | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at`  | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |

## `permission_group_permissions`

| Campo                 | Tipo        | Restrições                  |
| --------------------- | ----------- | --------------------------- |
| `id`                  | `SERIAL`    | PK                          |
| `permission_group_id` | `INTEGER`   | FK → `permission_groups.id` |
| `permission_id`       | `INTEGER`   | FK → `permissions.id`       |
| `is_active`           | `BOOLEAN`   | DEFAULT `TRUE` (só A)       |
| `created_at`          | `TIMESTAMP` | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at`          | `TIMESTAMP` | DEFAULT `CURRENT_TIMESTAMP` |

## `employees`

| Campo                 | Tipo              | Restrições                  |
| --------------------- | ----------------- | --------------------------- |
| `id`                  | `SERIAL`          | PK                          |
| `cpf`                 | `CHAR(11)`        | NOT NULL, UNIQUE            |
| `company_id`          | `INTEGER`         | FK → `companies.id` (só A)  |
| `permission_group_id` | `INTEGER`         | NOT NULL, FK → `permission_groups.id` |
| `unit_id`             | `INTEGER`         | FK → `units.id` (só A)      |
| `sector_id`           | `INTEGER`         | NOT NULL, FK → `sectors.id` |
| `name`                | `VARCHAR(255)`    | NOT NULL                    |
| `email`               | `VARCHAR(255)`    | NOT NULL                    |
| `phone`               | `VARCHAR(20)`     |                             |
| `password_hash`       | `VARCHAR(255)`    | NOT NULL                    |
| `status`              | `status_employee` | NOT NULL                    |
| `storage_file_id`     | `INTEGER`         | FK → `storage_files.id`     |
| `is_active`           | `BOOLEAN`         | DEFAULT `TRUE` (só A)       |
| `created_at`          | `TIMESTAMP`       | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at`          | `TIMESTAMP`       | DEFAULT `CURRENT_TIMESTAMP` |

# Subscription

## `plans`

| Campo           | Tipo            | Restrições                          |
| --------------- | --------------- | ----------------------------------- |
| `id`            | `SERIAL`        | PK                                  |
| `name`          | `VARCHAR(100)`  | NOT NULL                            |
| `description`   | `VARCHAR(255)`  |                                     |
| `price`         | `NUMERIC(12,2)` | NOT NULL, CHECK `price >= 0`        |
| `duration_days` | `INTEGER`       | NOT NULL, CHECK `duration_days > 0` |
| `currency`      | `VARCHAR(10)`   | NOT NULL, DEFAULT `'Reais'` (só A)  |
| `is_active`     | `BOOLEAN`       | DEFAULT `TRUE` (só A)               |
| `created_at`    | `TIMESTAMP`     | DEFAULT `CURRENT_TIMESTAMP`         |
| `updated_at`    | `TIMESTAMP`     | DEFAULT `CURRENT_TIMESTAMP`         |

## `subscriptions`

| Campo            | Tipo        | Restrições                  |
| ---------------- | ----------- | --------------------------- |
| `id`             | `SERIAL`    | PK                          |
| `company_id`     | `INTEGER`   | FK → `companies.id`         |
| `plan_id`        | `INTEGER`   | FK → `plans.id`             |
| `is_active`      | `BOOLEAN`   | DEFAULT `TRUE`              |
| `installments`   | `BOOLEAN`   | DEFAULT `TRUE`              |
| `deactivated_at` | `TIMESTAMP` |                             |
| `created_at`     | `TIMESTAMP` | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at`     | `TIMESTAMP` | DEFAULT `CURRENT_TIMESTAMP` |

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

`src/worker.py` (`prepare`) cria a tabela e os triggers se não existirem. `INSERT`/`UPDATE`: `FOR EACH STATEMENT`. `DELETE`: `FOR EACH ROW` com `row_pk`. Canal `aether_rpa`. Triggers nas 11 tabelas de negócio do contrato: `addresses`, `storage_files`, `permission_groups`, `permissions`, `plans`, `companies`, `units`, `sectors`, `permission_group_permissions`, `employees`, `subscriptions`. Só banco A. Conexões do RPA usam `application_name=aether-rpa` e os triggers ignoram esses writes.

# Relacionamentos (contrato RPA)

| Origem                                             | Destino                   |
| -------------------------------------------------- | ------------------------- |
| `companies.address_id`                             | `addresses.id`            |
| `units.company_id`                                 | `companies.id`            |
| `units.address_id`                                 | `addresses.id`            |
| `sectors.unit_id`                                  | `units.id`                |
| `sectors.company_id`                               | `companies.id`            |
| `permission_groups.company_id`                     | `companies.id`            |
| `permission_group_permissions.permission_group_id` | `permission_groups.id`    |
| `permission_group_permissions.permission_id`       | `permissions.id`          |
| `employees.storage_file_id`                        | `storage_files.id`        |
| `employees.sector_id`                              | `sectors.id`              |
| `employees.permission_group_id`                    | `permission_groups.id`    |
| `subscriptions.plan_id`                            | `plans.id`                |
| `subscriptions.company_id`                         | `companies.id`            |

# Índices

Índices adicionais podem ser criados pelo worker em `prepare`. Os FKs acima definem os joins principais do contrato.
