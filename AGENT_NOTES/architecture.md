Pacotes na raiz = tabelas do banco B. definition.py: RegisterA/TableA e RegisterB/TableB; EmployeeStatus só em employee/definition.py.
extractor: extract_from_a/b; fetch em shared.extract. transformer: transform_to_b/a(connection) chama extract e shared.transform (FIELD_MAP A→B; {} se schema idêntico).
driver: drive_to_a/b(connection_a, connection_b, operation); shared.drive faz INSERT (com PK) ou UPDATE; delete fora; PK composta em permission_group_employee.
