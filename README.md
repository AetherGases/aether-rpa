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

| Variável | Descrição |
| -------- | --------- |
| `DATABASE_A_URL` | URL libpq do banco A (cadastral) |
| `DATABASE_B_URL` | URL libpq do banco B (core) |

Exemplo (copie `.env.example` e ajuste):

```
DATABASE_A_URL=postgresql://user:password@localhost:5432/aether_a
DATABASE_B_URL=postgresql://user:password@localhost:5432/aether_b
```

## Executar o worker

```bash
python -m src.worker
```

O processo é um **daemon de longa duração**: mantém conexões abertas com A e B, processa a fila e escuta novos eventos.

### Ciclo de vida

1. **Prepare (A e B)** — em cada banco, cria `rpa_outbox`, funções PL/pgSQL e triggers nas tabelas sincronizadas, se ainda não existirem.
2. **Drain inicial** — esvazia pendências (`processed_at IS NULL`) do outbox de A → B e de B → A, respeitando ordem de FK (pais → filhos no insert/update; filhos → pais no delete).
3. **Listen** — `LISTEN aether_rpa` nos dois bancos; a cada `NOTIFY`, drena o outbox da origem correspondente e replica para o destino.

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
| `src/worker.py` | Prepare DDL, conexões, entrypoint |

## Testes

```bash
pytest tests/ -v --cov --cov-report=term-missing
```
