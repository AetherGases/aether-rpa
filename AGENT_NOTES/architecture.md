ETL em src/: definition, extractor, transformer, driver (UPSERT), orchestrator (A↔B + LISTEN), worker daemon.
Conexão: `src/db_url.py` monta DSN de `POSTGRES_*` (A=`POSTGRES_DB_FIRST_YEAR`, B=`POSTGRES_DB`); `DATABASE_A_URL`/`DATABASE_B_URL` opcionais sobrescrevem.
Triggers nos dois bancos; application_name=aether-rpa evita loop. python -m src.worker.
Schema 2026-09: B SQL congelado; A SQL pode ganhar colunas do contrato RPA; permission_group_employees fora dos dois bancos; tipo no transformer (installments false↔0, true↔1, >0↔true); status_employee/EMPLOYEE_STATUS unificados (ACTIVE, INACTIVE, IN_VACATION) com passthrough no transformer.
Contrato RPA 2026-09-25: 11 tabelas; A SQL em new_first_year_database.sql com colunas do contrato e country nullable para B→A.
Dockerfile: defaults POSTGRES_PORT/POSTGRES_SSLMODE; demais POSTGRES_* injetados no deploy (EKS).
