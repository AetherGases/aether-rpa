ETL em src/: definition, extractor, transformer, driver (UPSERT), orchestrator (A↔B + LISTEN), worker daemon.
Triggers nos dois bancos; application_name=aether-rpa evita loop. python -m src.worker.
Schema 2026-09: B SQL congelado; A SQL pode ganhar colunas do contrato RPA; permission_group_employees fora dos dois bancos; tipo no transformer (installments false↔0, true↔1, >0↔true); status_employee unificado nos dois bancos (passthrough no transformer).
Contrato RPA 2026-09-25: 11 tabelas; A SQL em new_first_year_database.sql com colunas do contrato e country nullable para B→A.
