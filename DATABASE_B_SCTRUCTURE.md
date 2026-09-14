# Modelo de Dados

## Enums

### `EMPLOYEE_STATUS`

| Valor         |
| ------------- |
| `ACTIVE`      |
| `INACTIVE`    |
| `IN_VACATION` |

# Tabelas administrativas e institucionais

## `address`

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
| `created_at`   | `TIMESTAMP`    | DEFAULT `current_timestamp` |
| `updated_at`   | `TIMESTAMP`    |                             |

## `enterprise`

| Campo        | Tipo           | Restrições                  |
| ------------ | -------------- | --------------------------- |
| `id`         | `SERIAL`       | PK                          |
| `name`       | `VARCHAR(150)` | NOT NULL                    |
| `trade_name` | `VARCHAR(150)` |                             |
| `cnpj`       | `CHAR(14)`     | NOT NULL, UNIQUE            |
| `created_at` | `TIMESTAMP`    | DEFAULT `current_timestamp` |
| `updated_at` | `TIMESTAMP`    |                             |
| `id_address` | `INTEGER`      | FK → `address.id`           |

## `unit`

| Campo           | Tipo        | Restrições                  |
| --------------- | ----------- | --------------------------- |
| `id`            | `SERIAL`    | PK                          |
| `cnae`          | `CHAR(7)`   |                             |
| `cnpj`          | `CHAR(14)`  | NOT NULL, UNIQUE            |
| `is_active`     | `BOOLEAN`   | NOT NULL, DEFAULT `true`    |
| `created_at`    | `TIMESTAMP` | DEFAULT `current_timestamp` |
| `updated_at`    | `TIMESTAMP` |                             |
| `id_enterprise` | `INTEGER`   | FK → `enterprise.id`        |
| `id_address`    | `INTEGER`   | FK → `address.id`           |

## `department`

| Campo         | Tipo           | Restrições                         |
| ------------- | -------------- | ---------------------------------- |
| `id`          | `SERIAL`       | PK                                 |
| `name`        | `VARCHAR(150)` | NOT NULL                           |
| `description` | `VARCHAR(150)` |                                    |
| `created_at`  | `TIMESTAMP`    | DEFAULT `current_timestamp`        |
| `updated_at`  | `TIMESTAMP`    |                                    |
| `id_unit`     | `INTEGER`      | FK → `unit.id`, ON DELETE RESTRICT |

## `storage_file`

| Campo        | Tipo           | Restrições                  |
| ------------ | -------------- | --------------------------- |
| `id`         | `SERIAL`       | PK                          |
| `name`       | `VARCHAR(150)` | NOT NULL                    |
| `path`       | `VARCHAR(255)` | NOT NULL                    |
| `created_at` | `TIMESTAMP`    | DEFAULT `current_timestamp` |
| `updated_at` | `TIMESTAMP`    |                             |

## `permission_group`

| Campo         | Tipo           | Restrições                  |
| ------------- | -------------- | --------------------------- |
| `id`          | `SERIAL`       | PK                          |
| `description` | `VARCHAR(150)` | NOT NULL                    |
| `created_at`  | `TIMESTAMP`    | DEFAULT `current_timestamp` |

## `permission`

| Campo         | Tipo           | Restrições                  |
| ------------- | -------------- | --------------------------- |
| `id`          | `SERIAL`       | PK                          |
| `name`        | `VARCHAR(150)` | NOT NULL                    |
| `description` | `VARCHAR(150)` |                             |
| `url`         | `VARCHAR(255)` | NOT NULL                    |
| `created_at`  | `TIMESTAMP`    | DEFAULT `current_timestamp` |
| `updated_at`  | `TIMESTAMP`    |                             |

## `permission_group_permission`

| Campo                 | Tipo        | Restrições                  |
| --------------------- | ----------- | --------------------------- |
| `id`                  | `SERIAL`    | PK                          |
| `created_at`          | `TIMESTAMP` | DEFAULT `current_timestamp` |
| `updated_at`          | `TIMESTAMP` |                             |
| `id_permission`       | `INTEGER`   | FK → `permission.id`        |
| `id_permission_group` | `INTEGER`   | FK → `permission_group.id`  |

### Constraints adicionais

| Constraint                       | Campos                                          |
| -------------------------------- | ----------------------------------------------- |
| `uq_permission_group_permission` | UNIQUE (`id_permission`, `id_permission_group`) |

## `employee`

| Campo             | Tipo              | Restrições                  |
| ----------------- | ----------------- | --------------------------- |
| `id`              | `SERIAL`          | PK                          |
| `cpf`             | `CHAR(11)`        | NOT NULL, UNIQUE            |
| `name`            | `VARCHAR(150)`    | NOT NULL                    |
| `email`           | `VARCHAR(255)`    | NOT NULL, UNIQUE            |
| `phone`           | `VARCHAR(20)`     | NOT NULL                    |
| `password_hash`   | `VARCHAR(255)`    | NOT NULL                    |
| `employee_status` | `EMPLOYEE_STATUS` | NOT NULL                    |
| `created_at`      | `TIMESTAMP`       | DEFAULT `current_timestamp` |
| `updated_at`      | `TIMESTAMP`       |                             |
| `id_storage_file` | `INTEGER`         | FK → `storage_file.id`      |
| `id_department`   | `INTEGER`         | FK → `department.id`        |

## `permission_group_employee`

| Campo                 | Tipo      | Restrições                     |
| --------------------- | --------- | ------------------------------ |
| `id_employee`         | `INTEGER` | PK, FK → `employee.id`         |
| `id_permission_group` | `INTEGER` | PK, FK → `permission_group.id` |

### Chave primária composta

`(id_employee, id_permission_group)`

## `plan`

| Campo           | Tipo           | Restrições                          |
| --------------- | -------------- | ----------------------------------- |
| `id`            | `SERIAL`       | PK                                  |
| `name`          | `VARCHAR(50)`  | NOT NULL, UNIQUE                    |
| `description`   | `VARCHAR(150)` |                                     |
| `price`         | `NUMERIC`      | NOT NULL, CHECK `price >= 0`        |
| `duration_days` | `INTEGER`      | NOT NULL, CHECK `duration_days > 0` |
| `is_active`     | `BOOLEAN`      | NOT NULL, DEFAULT `true`            |
| `created_at`    | `TIMESTAMP`    | DEFAULT `current_timestamp`         |
| `updated_at`    | `TIMESTAMP`    |                                     |

## `plan_subscription`

| Campo            | Tipo        | Restrições                          |
| ---------------- | ----------- | ----------------------------------- |
| `id`             | `SERIAL`    | PK                                  |
| `is_active`      | `BOOLEAN`   | NOT NULL, DEFAULT `true`            |
| `installments`   | `INTEGER`   | NOT NULL, CHECK `installments >= 0` |
| `created_at`     | `TIMESTAMP` | DEFAULT `current_timestamp`         |
| `deactivated_at` | `TIMESTAMP` |                                     |
| `id_plan`        | `INTEGER`   | FK → `plan.id`, ON DELETE CASCADE   |
| `id_enterprise`  | `INTEGER`   | FK → `enterprise.id`                |

# Relacionamentos

| Origem                                            | Destino                | Comportamento      |
| ------------------------------------------------- | ---------------------- | ------------------ |
| `enterprise.id_address`                           | `address.id`           |                    |
| `unit.id_enterprise`                              | `enterprise.id`        |                    |
| `unit.id_address`                                 | `address.id`           |                    |
| `department.id_unit`                              | `unit.id`              | ON DELETE RESTRICT |
| `permission_group_permission.id_permission`       | `permission.id`        |                    |
| `permission_group_permission.id_permission_group` | `permission_group.id`  |                    |
| `employee.id_storage_file`                        | `storage_file.id`      |                    |
| `employee.id_department`                          | `department.id`        |                    |
| `permission_group_employee.id_employee`           | `employee.id`          |                    |
| `permission_group_employee.id_permission_group`   | `permission_group.id`  |                    |
| `plan_subscription.id_plan`                       | `plan.id`              | ON DELETE CASCADE  |
| `plan_subscription.id_enterprise`                 | `enterprise.id`        |                    |

# Índices

| Índice                                                | Tabela                        | Campo                   |
| ----------------------------------------------------- | ----------------------------- | ----------------------- |
| `idx_enterprise_id_address`                           | `enterprise`                  | `id_address`            |
| `idx_unit_id_enterprise`                              | `unit`                        | `id_enterprise`         |
| `idx_unit_id_address`                                 | `unit`                        | `id_address`            |
| `idx_department_id_unit`                              | `department`                  | `id_unit`               |
| `idx_permission_group_permission_id_permission`       | `permission_group_permission` | `id_permission`         |
| `idx_permission_group_permission_id_permission_group` | `permission_group_permission` | `id_permission_group`   |
| `idx_employee_id_storage_file`                        | `employee`                    | `id_storage_file`       |
| `idx_employee_id_department`                          | `employee`                    | `id_department`         |
| `idx_employee_status`                                 | `employee`                    | `employee_status`       |
| `idx_plan_subscription_id_plan`                       | `plan_subscription`           | `id_plan`               |
| `idx_plan_subscription_id_enterprise`                 | `plan_subscription`           | `id_enterprise`         |

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

`src/worker.py` (`prepare`) cria a tabela e os triggers se não existirem. `INSERT`/`UPDATE`: `FOR EACH STATEMENT`. `DELETE`: `FOR EACH ROW` com `row_pk`. Canal `aether_rpa`. Triggers nas tabelas: `address`, `enterprise`, `unit`, `department`, `storage_file`, `permission_group`, `permission`, `permission_group_permission`, `employee`, `permission_group_employee`, `plan`, `plan_subscription`. Só banco B.
