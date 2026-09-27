# Alinhamento de schema A/B e viabilidade do RPA

**Status:** Ready

## Contexto

Os bancos A (cadastral, primeiro ano) e B (core, segundo ano) foram revistos. Os artefatos de origem na raiz são `new_first_year_database.sql` (A) e `new_second_year_database.sql` (B). O RPA hoje replica um contrato A↔B descrito em `DATABASE_A_STRUCTURE.md` / `DATABASE_B_SCTRUCTURE.md` e em `src/definition.py`.

Há dúvida se as mudanças quebram a replicação. O RPA precisa permanecer viável **sem incluir tabelas novas** e **sem alterar o banco B**. O que faltar na origem A para alimentar o contrato com B deve ser acrescentado no SQL de A. Divergências de tipo, enum e nome de campo já existentes nos dois lados são resolvidas na camada de transformação já existente.

## Objetivo

Manter a replicação bidirecional das tabelas de negócio já cobertas pelo RPA, alinhando a documentação e o contrato de sincronização aos schemas novos, com A ajustável e B congelado.

## Fora de escopo

* Incluir no RPA tabelas que não estão em `DATABASE_A_STRUCTURE.md` (por exemplo `payments`, `inventories`, `administrators`, `telephone_companies`, `contracts`, gases/ROI e equivalentes em B).
* Alterar `new_second_year_database.sql` ou qualquer outro artefato de schema do banco B.
* Restaurar ou sincronizar `permission_group_employees` / `permission_group_employee`.
* Migrar dados já persistidos em ambientes reais; o contrato vale sobre os artefatos SQL/markdown do repositório e sobre o comportamento do worker.
* Planejamento técnico de implementação (estrutura interna de módulos além do papel já existente da transformação).

## Atores

* **RPA (worker):** lê outbox, transforma e escreve A↔B.
* **Banco A:** origem/destino cadastral; SQL no repositório pode ser atualizado.
* **Banco B:** origem/destino core; schema congelado.

## Cenários do usuário

### Documentar os schemas vigentes

Operação e desenvolvimento passam a ler markdowns que descrevem A após os acréscimos necessários ao RPA, e B exatamente como no SQL novo.

#### Critérios de aceitação

1. Given os SQLs da raiz e as regras desta spec
   When a documentação de A for atualizada
   Then `DATABASE_A_STRUCTURE.md` descreve as tabelas/colunas/enums/FKs do `new_first_year_database.sql` já ajustado, **sem** `permission_group_employees`, e mantém a seção de `rpa_outbox`.
2. Given o SQL congelado de B
   When a documentação de B for atualizada
   Then `DATABASE_B_SCTRUCTURE.md` descreve `new_second_year_database.sql` **sem** `permission_group_employee`, e mantém a seção de `rpa_outbox`.

### Restaurar na origem A o que B ainda exige

Colunas ou tabelas do contrato RPA que sumiram do SQL novo de A voltam a existir em A, para que a origem tenha o dado. B não muda.

#### Critérios de aceitação

1. Given uma tabela do RPA que existe em B e um campo obrigatório em B sem coluna correspondente em A
   When o SQL de A for ajustado
   Then a coluna (ou a tabela inteira, no caso de `storage_files`) existe em `new_first_year_database.sql` com restrição suficiente para B aceitar o valor.
2. Given colunas novas de A que B não possui (`country`, `email`, `units.name`, `currency`, `is_active` extra, etc.)
   When o SQL de A for ajustado
   Then essas colunas **permanecem** em A e **não** entram no mapeamento de replicação.
3. Given uma coluna só de A hoje `NOT NULL` sem default e sem correspondente em B
   When o RPA escrever B→A
   Then o SQL de A permite a ausência (NULL ou DEFAULT), para a escrita não falhar por falta de dado em B.

### Replicar só o conjunto autorizado, com conversão na transformação

O pipeline continua bidirecional nas tabelas do teto `DATABASE_A_STRUCTURE.md`, menos a N:N removida. Tipo, enum e nomes divergentes são convertidos na transformação, nos dois sentidos.

#### Critérios de aceitação

1. Given uma alteração em tabela autorizada no banco origem
   When o worker drenar o outbox
   Then o destino recebe insert/update/delete equivalente nas colunas mapeadas, respeitando ordem de FK.
2. Given `permission_group_employees`
   When o worker preparar triggers e mapear tabelas
   Then essa tabela não é escutada, extraída nem escrita em A nem em B.
3. Given `storage_files` / `storage_file`
   When o contrato for aplicado
   Then a tabela existe em A, permanece em B e continua no RPA.
4. Given um registro de colaborador com `status` em A
   When for replicado para B e de volta para A
   Then vale o mapeamento de enum desta spec (incluindo a perda `dismissed` → `INACTIVE` → `on leave`).
5. Given `subscriptions.installments` em A (`true` ou `false`) ou em B (inteiro `>= 0`)
   When for replicado na transformação
   Then vale FR-012 (incluindo a perda `12` → `true` → `1`).

## Requisitos

### Requisitos funcionais

* FR-001: O conjunto sincronizado pelo RPA é exatamente as tabelas de negócio documentadas hoje em `DATABASE_A_STRUCTURE.md`, **exceto** `permission_group_employees`. Tabelas novas dos SQLs não entram no RPA.
* FR-002: `permission_group_employees` / `permission_group_employee` é retirada do contrato dos dois bancos: não consta do SQL de A, não é reintroduzida no SQL de B, sai dos dois markdowns e sai do RPA. Em B o SQL novo já não a contém; isso permanece.
* FR-003: `new_second_year_database.sql` não é modificado.
* FR-004: `new_first_year_database.sql` recebe as tabelas/colunas ausentes necessárias ao contrato com B (lista em Entidades). Colunas extras já presentes em A são preservadas.
* FR-005: `DATABASE_A_STRUCTURE.md` e `DATABASE_B_SCTRUCTURE.md` são atualizados para refletir os SQLs vigentes após FR-002, FR-003 e FR-004, incluindo `rpa_outbox` e a lista de tabelas com trigger.
* FR-006: A replicação permanece bidirecional (A→B e B→A) para as tabelas de FR-001, com UPSERT no destino, outbox + LISTEN e ignorar writes com `application_name=aether-rpa`.
* FR-007: Nomes de coluna diferentes com o mesmo significado (padrão `x_id` ↔ `id_x`, `sector_id` ↔ `id_department`, `permission_groups.name` ↔ `permission_group.description`) são convertidos na transformação, nos dois sentidos.
* FR-008: Tipos incompatíveis que **já existem nos dois lados** não são “corrigidos” mudando o tipo persistido em A; a conversão ocorre na transformação. Conversões obrigatórias: `addresses.number` (`VARCHAR` ↔ `INTEGER`); `subscriptions.installments` (`BOOLEAN` ↔ `INTEGER`, FR-012).
* FR-009: Enum de colaborador na transformação:
  * A→B: `active`→`ACTIVE`; `on vacation`→`IN_VACATION`; `on leave`→`INACTIVE`; `dismissed`→`INACTIVE`
  * B→A: `ACTIVE`→`active`; `IN_VACATION`→`on vacation`; `INACTIVE`→`on leave`
* FR-010: A ordem de replicação respeita FKs do schema ajustado (pais antes de filhos no insert/update; inversa no delete), incluindo `permission_groups` depois de `companies` quando `company_id` / `id_enterprise` estiver mapeado.
* FR-011: Valor que não puder ser convertido para o tipo do destino (por exemplo `number` não numérico, `installments` nulo em A, texto maior que o destino) não é escrito no destino; o evento não é tratado como replicação bem-sucedida.
* FR-012: `subscriptions.installments` na transformação:
  * A→B: `false`→`0`; `true`→`1`
  * B→A: `0`→`false`; qualquer inteiro `> 0`→`true`
  * A não origina inteiros diferentes de `0` e `1`; valores `> 1` só existem se gravados em B.

### Requisitos não funcionais

* NFR-001: A viabilidade do RPA, após FR-004 e as conversões, cobre as 11 tabelas de FR-001; não se declara inviável uma tabela só porque o nome ou o tipo do campo diverge, desde que a transformação tenha regra.
* NFR-002: A suíte existente continua sendo o critério de verificação do pipeline (`pytest tests/ -v --cov --cov-report=term-missing` com cobertura total e testes verdes), incluindo os novos mapeamentos e conversões.

## Casos de borda e falhas

* Round-trip de colaborador: `dismissed` vira `INACTIVE` e, na volta, `on leave`. Essa perda é aceita.
* Round-trip de `INACTIVE` nunca recria `dismissed`.
* Round-trip de assinatura: inteiro `> 1` em B vira `true` em A e, na ida seguinte, vira `1` em B. Essa perda é aceita.
* `installments` nulo em A não equivale a `true` nem a `false`; aplica-se FR-011.
* Colunas só de A não são apagadas nem sobrescritas com nulo quando o evento vem de B, salvo se o próprio campo estiver no mapeamento.
* Tabela desconhecida no outbox permanece com o comportamento atual (não dirige replicação de negócio).
* `units.cnpj` / `units.cnae` e `permissions.url` podem ser mais longos em A do que B aceita: aplica-se FR-011.
* `plans.price` e CHECKs de A que rejeitariam um valor válido em B devem ser relaxados no SQL de A (B não muda).

## Entidades relevantes

Tabelas no RPA (nome A → nome B):

* `addresses` → `address`
* `storage_files` → `storage_file` (tabela inteira a recriar em A)
* `permission_groups` → `permission_group`
* `permissions` → `permission`
* `plans` → `plan`
* `companies` → `enterprise`
* `units` → `unit`
* `sectors` → `department`
* `permission_group_permissions` → `permission_group_permission`
* `employees` → `employee`
* `subscriptions` → `plan_subscription`

Acréscimos mínimos no SQL de A (além de preservar colunas extras atuais):

* `addresses`: `zip_code`, `neighborhood`; `state` volta a ser exigível como no contrato com B
* `companies`: `trade_name`, `cnpj` (obrigatório e único, compatível com B)
* `sectors`: `name` (obrigatório, equivalente a `department.name`)
* `storage_files`: tabela completa alinhada a `storage_file`
* `permissions`: `url` (obrigatório)
* `plans`: `duration_days` (obrigatório, `> 0`)
* `employees`: `cpf` (obrigatório, único), `phone`, `password_hash` (obrigatório), `storage_file_id`, `sector_id` (obrigatório, equivalente a `id_department`); `permission_group_id` obrigatório (equivalente a `id_permission_group`)
* `subscriptions`: `deactivated_at`

Mapeamentos de nome além do padrão `*_id` ↔ `id_*`:

* `permission_groups.name` ↔ `permission_group.description`
* `employees.status` ↔ `employee.employee_status` (com FR-009)
* `employees.sector_id` ↔ `employee.id_department`
* `subscriptions.installments` (`BOOLEAN` ↔ `INTEGER`, com FR-012)

Fora do RPA, permanecem no SQL de A se já existirem: telefone, contratos, inventários, pagamentos, ROI, gases, selo, administradores e demais tabelas novas.

## Dependências

* Schemas de origem: `new_first_year_database.sql`, `new_second_year_database.sql`
* Contrato atual de tabelas A: `DATABASE_A_STRUCTURE.md`
* Worker atual: outbox, triggers, `LISTEN`/`NOTIFY`, transformação e UPSERT já existentes
* Banco B congelado como publicado em `new_second_year_database.sql`

## Premissas

* `new_first_year_database.sql` corresponde ao banco A e `new_second_year_database.sql` ao banco B.
* “Atualizar o pipeline” significa atualizar o contrato de replicação (mapeamento, transformação, triggers/outbox e testes), não o workflow de CI em si, salvo se os testes da suíte já forem o job de CI.
* Conversão de `addresses.number`: A→B interpreta o texto como inteiro; B→A serializa o inteiro em texto.
* Campos extras só de A ficam fora do mapeamento.
* Relaxar `NOT NULL` sem default (ou acrescentar DEFAULT) em colunas só de A é permitido e necessário para B→A.

## Critérios de sucesso

* SC-001: Os dois markdowns de banco descrevem os SQLs vigentes e não documentam `permission_group_employees` / `permission_group_employee`.
* SC-002: O SQL de B no repositório é idêntico ao atual.
* SC-003: As 11 tabelas de FR-001 têm par A↔B documentado, com origem A capaz de fornecer os campos que B exige.
* SC-004: A suíte de testes cobre o conjunto sincronizado (sem a N:N removida, com `storage_files` e com as conversões de FR-007, FR-008, FR-009 e FR-012) e fecha 100% verde.
