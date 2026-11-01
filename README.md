# Aether RPA

ETL bidirecional em Python entre o **banco A** (cadastral) e o **banco B** (core), ambos PostgreSQL. O worker replica alterações detectadas via outbox + `LISTEN`/`NOTIFY`.

## Requisitos

- Python 3.11+
- Dois bancos PostgreSQL acessíveis (schemas descritos em `DATABASE_A_STRUCTURE.md` e `DATABASE_B_SCTRUCTURE.md`)

## Instalação

```bash
pip install -r requirements.txt
```

## Variáveis de ambiente

Em produção, A e B costumam estar no **mesmo cluster PostgreSQL**, com credenciais compartilhadas e nomes de banco distintos (GitHub Environments / Secrets):

| Variável | Descrição |
| -------- | --------- |
| `POSTGRES_USER` | Usuário (banco **B**) |
| `POSTGRES_PASSWORD` | Senha (banco **B**) |
| `RPA_POSTGRES_USER` | Usuário dedicado do RPA no banco **A** (`rpa_aether`) |
| `RPA_POSTGRES_PASSWORD` | Senha do usuário dedicado do RPA no banco **A** |
| `POSTGRES_HOST` | Host do cluster |
| `POSTGRES_PORT` | Porta (ex.: `5432`) |
| `POSTGRES_SSLMODE` | Modo SSL libpq (ex.: `require`) |
| `POSTGRES_DB_FIRST_YEAR` | Nome do banco **A** (cadastral / primeiro ano) |
| `POSTGRES_DB` | Nome do banco **B** (core / segundo ano) |

O worker monta as URLs de conexão a partir dessas variáveis (`sslmode` na query string).

Para desenvolvimento local, ainda é possível definir URLs completas (têm precedência):

| Variável | Descrição |
| -------- | --------- |
| `RPA_DATABASE_A_URL` | URL libpq do banco A no host direto, sem pooler (opcional; tem prioridade sobre `DATABASE_A_URL`) |
| `RPA_DATABASE_B_URL` | URL libpq do banco B no host direto, sem pooler (opcional; tem prioridade sobre `DATABASE_B_URL`) |
| `DATABASE_A_URL` | URL libpq do banco A (opcional) |
| `DATABASE_B_URL` | URL libpq do banco B (opcional) |

Exemplo: copie `.env.example` e ajuste.

## Executar o worker

```bash
python -m src.worker
```

O processo é um **daemon de longa duração**: mantém conexões abertas com A e B, processa a fila e escuta novos eventos.

### Ciclo de vida

Pré-requisito: `rpa_outbox`, funções PL/pgSQL e triggers já instalados nos dois bancos pelo script `init-postgres/13-rpa-outbox-triggers.sql` do `aether-toolskit` (executado pelo owner do banco). O RPA não executa DDL.

1. **Drain inicial** — esvazia pendências (`processed_at IS NULL`) do outbox de A → B e de B → A, respeitando ordem de FK (pais → filhos no insert/update; filhos → pais no delete).
2. **Listen** — `LISTEN aether_rpa` nos dois bancos; a cada `NOTIFY`, drena o outbox da origem correspondente e replica para o destino.

Detalhes das tabelas e triggers: seção **RPA** em `DATABASE_A_STRUCTURE.md` (banco A) e `DATABASE_B_SCTRUCTURE.md` (banco B).

### Prevenção de loop

Conexões do RPA usam `application_name=aether-rpa`. Os triggers de outbox **ignoram** writes feitos com esse `application_name`, para que a replicação A→B (ou B→A) não gere novos eventos no banco de destino.

### Escrita no destino

Insert no destino usa **UPSERT** (`INSERT … ON CONFLICT` na PK) para re-sync idempotente. Update e delete seguem PK mapeada entre A e B.

## Estrutura do código

| Módulo | Papel |
| ------ | ----- |
| `src/definition.py` | Tipos, mapeamento A↔B, ordem de FK |
| `src/extractor.py` | Leitura no banco origem |
| `src/transformer.py` | Conversão de colunas A↔B |
| `src/driver.py` | Insert/update/delete no destino |
| `src/orchestrator.py` | Drain do outbox + `LISTEN` |
| `src/worker.py` | Conexões, entrypoint |

## Testes

```bash
pytest tests/ -v --cov --cov-report=term-missing
```
