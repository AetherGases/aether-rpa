ETL em src/: definition, extractor, transformer, driver (UPSERT), orchestrator (A↔B + LISTEN), worker daemon.
Conexão: `src/db_url.py` monta DSN de `POSTGRES_*` (A=`POSTGRES_DB_FIRST_YEAR` com `RPA_POSTGRES_USER`/`RPA_POSTGRES_PASSWORD`, B=`POSTGRES_DB` com `POSTGRES_USER`/`POSTGRES_PASSWORD`); `RPA_DATABASE_A_URL`/`RPA_DATABASE_B_URL` (host direto, sem pooler) e depois `DATABASE_A_URL`/`DATABASE_B_URL` sobrescrevem.
2026-10-31: _listen faz commit após LISTEN (LISTEN só vale no commit; Neon mata idle in transaction após 5 min). LISTEN exige host direto do Neon, não o -pooler.
Triggers nos dois bancos, instalados pelo aether-toolskit (init-postgres/13-rpa-outbox-triggers.sql), não pelo worker; application_name=aether-rpa evita loop. python -m src.worker.
Schema 2026-09: B SQL congelado; A SQL pode ganhar colunas do contrato RPA; permission_group_employees fora dos dois bancos; tipo no transformer (installments false↔0, true↔1, >0↔true); status_employee/EMPLOYEE_STATUS unificados (ACTIVE, INACTIVE, IN_VACATION) com passthrough no transformer.
Contrato RPA 2026-09-25: 11 tabelas; A SQL em new_first_year_database.sql com colunas do contrato e country nullable para B→A.
Dockerfile: defaults POSTGRES_PORT/POSTGRES_SSLMODE; demais POSTGRES_* injetados no deploy (EKS).
2026-10-31: A e B usam permissions.pattern (A: permissions, B: permission); field_map vazio.
2026-11-02: driver faz um UPSERT por linha em SAVEPOINT (insert e update são iguais): linha com erro de dado/integridade é logada e pulada, não derruba o dreno; depois avança a sequence do destino. Dreno copia só as linhas do outbox.row_pk ({"id": n}); row_pk nulo (triggers antigos) = tabela inteira.
2026-11-02: A→B corta texto ao limite de B (TableSpec.truncate_b), CNAE vira 7 dígitos (senão NULL), número de endereço = 1º grupo de dígitos (senão 0), is_active=false do funcionário vira INACTIVE. B→A não sobrescreve o texto completo de A (TableSpec.conflict_a) e deriva employees.company_id/unit_id do departamento.
Em aberto: is_active de empresas/permissões/setores/endereços não existe em B (precisa de coluna nova, decisão de schema); colunas só de A (size, email, currency, country, units.name) não vão para B.
