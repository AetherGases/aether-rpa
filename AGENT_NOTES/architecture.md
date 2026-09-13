Pacotes na raiz = tabelas do banco B. definition.py: RegisterA/TableA (colunas do A) e RegisterB/TableB (colunas do B), nullable sem default, sem validação.
EmployeeStatus vive só em employee/definition.py. extractor: extract_from_a → TableA, extract_from_b → TableB; fetch comum em shared.extract; employee converte EmployeeStatus depois.
transformer: shared.transform + FIELD_MAP A→B nos 7 pacotes divergentes (transform_to_b/a); schema idêntico permanece vazio; driver ainda vazio.
