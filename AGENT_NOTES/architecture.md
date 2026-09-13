Pacotes na raiz = tabelas do banco B. definition/extractor/transformer/driver: extract origem, INSERT/UPDATE/DELETE destino.
orchestrator drena rpa_outbox no A e chama drive_to_b ou delete_rows no B.
cmd/worker/main.py injeta conexões; prepare.py cria outbox+triggers se faltarem.
