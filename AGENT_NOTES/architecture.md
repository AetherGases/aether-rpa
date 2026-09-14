ETL em src/: definition, extractor, transformer, driver (UPSERT), orchestrator (A↔B + LISTEN), worker daemon.
Triggers nos dois bancos; application_name=aether-rpa evita loop. python -m src.worker.
