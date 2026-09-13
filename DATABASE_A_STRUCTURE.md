# Modelo de Dados

## Enums

### `employee_status`

| Valor         |
| ------------- |
| `ACTIVE`      |
| `INACTIVE`    |
| `IN_VACATION` |

# Referências

## `addresses`

| Campo          | Tipo           | Restrições                  |
| -------------- | -------------- | --------------------------- |
| `id`           | `SERIAL`       | PK                          |
| `zip_code`     | `CHAR(8)`      |                             |
| `state`        | `VARCHAR(150)` | NOT NULL                    |
| `city`         | `VARCHAR(150)` | NOT NULL                    |
| `neighborhood` | `VARCHAR(150)` | NOT NULL                    |
| `street`       | `VARCHAR(150)` | NOT NULL                    |
| `number`       | `INTEGER`      | NOT NULL                    |
| `complement`   | `VARCHAR(150)` |                             |
| `created_at`   | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at`   | `TIMESTAMP`    |                             |

## `companies`

| Campo        | Tipo           | Restrições                  |
| ------------ | -------------- | --------------------------- |
| `id`         | `SERIAL`       | PK                          |
| `name`       | `VARCHAR(150)` | NOT NULL                    |
| `trade_name` | `VARCHAR(150)` |                             |
| `cnpj`       | `CHAR(14)`     | NOT NULL, UNIQUE            |
| `created_at` | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP`    |                             |
| `address_id` | `INTEGER`      | FK → `addresses.id`         |

## `units`

| Campo        | Tipo        | Restrições                  |
| ------------ | ----------- | --------------------------- |
| `id`         | `SERIAL`    | PK                          |
| `cnae`       | `CHAR(7)`   |                             |
| `cnpj`       | `CHAR(14)`  | NOT NULL, UNIQUE            |
| `is_active`  | `BOOLEAN`   | NOT NULL, DEFAULT `TRUE`    |
| `created_at` | `TIMESTAMP` | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP` |                             |
| `company_id` | `INTEGER`   | FK → `companies.id`         |
| `address_id` | `INTEGER`   | FK → `addresses.id`         |

## `sectors`

| Campo         | Tipo           | Restrições                         |
| ------------- | -------------- | ---------------------------------- |
| `id`          | `SERIAL`       | PK                                 |
| `name`        | `VARCHAR(150)` | NOT NULL                           |
| `description` | `VARCHAR(150)` |                                    |
| `created_at`  | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP`        |
| `updated_at`  | `TIMESTAMP`    |                                    |
| `unit_id`     | `INTEGER`      | FK → `units.id`, ON DELETE RESTRICT |

# Employees

## `storage_files`

| Campo        | Tipo           | Restrições                  |
| ------------ | -------------- | --------------------------- |
| `id`         | `SERIAL`       | PK                          |
| `name`       | `VARCHAR(150)` | NOT NULL                    |
| `path`       | `VARCHAR(255)` | NOT NULL                    |
| `created_at` | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP`    |                             |

## `permission_groups`

| Campo         | Tipo           | Restrições                  |
| ------------- | -------------- | --------------------------- |
| `id`          | `SERIAL`       | PK                          |
| `description` | `VARCHAR(150)` | NOT NULL                    |
| `created_at`  | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |

## `permissions`

| Campo         | Tipo           | Restrições                  |
| ------------- | -------------- | --------------------------- |
| `id`          | `SERIAL`       | PK                          |
| `name`        | `VARCHAR(150)` | NOT NULL                    |
| `description` | `VARCHAR(150)` |                             |
| `url`         | `VARCHAR(255)` | NOT NULL                    |
| `created_at`  | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at`  | `TIMESTAMP`    |                             |

## `permission_group_permissions`

| Campo                 | Tipo        | Restrições                  |
| --------------------- | ----------- | --------------------------- |
| `id`                  | `SERIAL`    | PK                          |
| `created_at`          | `TIMESTAMP` | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at`          | `TIMESTAMP` |                             |
| `permission_id`       | `INTEGER`   | FK → `permissions.id`       |
| `permission_group_id` | `INTEGER`   | FK → `permission_groups.id` |

### Constraints adicionais

| Constraint                       | Campos                                          |
| -------------------------------- | ----------------------------------------------- |
| `uq_permission_group_permissions` | UNIQUE (`permission_id`, `permission_group_id`) |

## `employees`

| Campo             | Tipo              | Restrições                  |
| ----------------- | ----------------- | --------------------------- |
| `id`              | `SERIAL`          | PK                          |
| `cpf`             | `CHAR(11)`        | NOT NULL, UNIQUE            |
| `name`            | `VARCHAR(150)`    | NOT NULL                    |
| `email`           | `VARCHAR(255)`    | NOT NULL, UNIQUE            |
| `phone`           | `VARCHAR(20)`     | NOT NULL                    |
| `password_hash`   | `VARCHAR(255)`    | NOT NULL                    |
| `employee_status` | `employee_status` | NOT NULL                    |
| `created_at`      | `TIMESTAMP`       | DEFAULT `CURRENT_TIMESTAMP` |
| `updated_at`      | `TIMESTAMP`       |                             |
| `storage_file_id` | `INTEGER`         | FK → `storage_files.id`     |
| `sector_id`       | `INTEGER`         | FK → `sectors.id`           |

## `permission_group_employees`

| Campo                 | Tipo      | Restrições                     |
| --------------------- | --------- | ------------------------------ |
| `employee_id`         | `INTEGER` | PK, FK → `employees.id`        |
| `permission_group_id` | `INTEGER` | PK, FK → `permission_groups.id` |

### Chave primária composta

`(employee_id, permission_group_id)`

# Subscription

## `plans`

| Campo           | Tipo           | Restrições                          |
| --------------- | -------------- | ----------------------------------- |
| `id`            | `SERIAL`       | PK                                  |
| `name`          | `VARCHAR(50)`  | NOT NULL, UNIQUE                    |
| `description`   | `VARCHAR(150)` |                                     |
| `price`         | `NUMERIC`      | NOT NULL, CHECK `price >= 0`        |
| `duration_days` | `INTEGER`      | NOT NULL, CHECK `duration_days > 0` |
| `is_active`     | `BOOLEAN`      | NOT NULL, DEFAULT `TRUE`            |
| `created_at`    | `TIMESTAMP`    | DEFAULT `CURRENT_TIMESTAMP`         |
| `updated_at`    | `TIMESTAMP`    |                                     |

## `subscriptions`

| Campo            | Tipo        | Restrições                          |
| ---------------- | ----------- | ----------------------------------- |
| `id`             | `SERIAL`    | PK                                  |
| `is_active`      | `BOOLEAN`   | NOT NULL, DEFAULT `TRUE`            |
| `installments`   | `INTEGER`   | NOT NULL, CHECK `installments >= 0` |
| `created_at`     | `TIMESTAMP` | DEFAULT `CURRENT_TIMESTAMP`         |
| `deactivated_at` | `TIMESTAMP` |                                     |
| `plan_id`        | `INTEGER`   | FK → `plans.id`, ON DELETE CASCADE  |
| `company_id`     | `INTEGER`   | FK → `companies.id`                 |

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

# Relacionamentos

| Origem                                             | Destino                   | Comportamento      |
| -------------------------------------------------- | ------------------------- | ------------------ |
| `companies.address_id`                             | `addresses.id`            |                    |
| `units.company_id`                                 | `companies.id`            |                    |
| `units.address_id`                                 | `addresses.id`            |                    |
| `sectors.unit_id`                                  | `units.id`                | ON DELETE RESTRICT |
| `permission_group_permissions.permission_id`       | `permissions.id`          |                    |
| `permission_group_permissions.permission_group_id` | `permission_groups.id`    |                    |
| `employees.storage_file_id`                        | `storage_files.id`        |                    |
| `employees.sector_id`                              | `sectors.id`              |                    |
| `permission_group_employees.employee_id`           | `employees.id`            |                    |
| `permission_group_employees.permission_group_id`   | `permission_groups.id`    |                    |
| `subscriptions.plan_id`                            | `plans.id`                | ON DELETE CASCADE  |
| `subscriptions.company_id`                         | `companies.id`            |                    |

# Índices

| Índice                                                | Tabela                        | Campo                   |
| ----------------------------------------------------- | ----------------------------- | ----------------------- |
| `idx_companies_address_id`                            | `companies`                   | `address_id`            |
| `idx_units_company_id`                                | `units`                       | `company_id`            |
| `idx_units_address_id`                                | `units`                       | `address_id`            |
| `idx_sectors_unit_id`                                 | `sectors`                     | `unit_id`               |
| `idx_permission_group_permissions_permission_id`      | `permission_group_permissions` | `permission_id`         |
| `idx_permission_group_permissions_permission_group_id` | `permission_group_permissions` | `permission_group_id`   |
| `idx_employees_storage_file_id`                       | `employees`                   | `storage_file_id`       |
| `idx_employees_sector_id`                             | `employees`                   | `sector_id`             |
| `idx_employees_employee_status`                       | `employees`                   | `employee_status`       |
| `idx_subscriptions_plan_id`                           | `subscriptions`               | `plan_id`               |
| `idx_subscriptions_company_id`                        | `subscriptions`               | `company_id`            |
