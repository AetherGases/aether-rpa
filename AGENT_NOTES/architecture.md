ETL em src/: definition (tipos+TABLES), extractor, transformer, driver, orchestrator, worker.
drive_to_a/b recebem table_key; delete usa row_pks (PK do outbox), sem extract.
Entrada: python -m src.worker.
