# Módulo 07 — Bancos de dados (Prática Guiada)

> Objetivo desta prática: colocar a mão em **dois mundos**. Protagonista: **DynamoDB** — criar
> tabela (Console e CLI), `put-item`/`get-item`/`query`/`scan` (e sentir por que scan é caro),
> e criar um **GSI**. Coadjuvante: **RDS MySQL** — criar uma instância Free Tier, conectar de
> verdade e **deletar corretamente** no teardown.
>
> **Abordagem:** Console web primeiro (pra ver), CLI depois (pra fixar). Cada passo explica o *porquê*.
>
> ⏱️ Tempo estimado: 75–90 min.

---

## ⚠️ Antes de começar — custos (leia mesmo)

- **DynamoDB: custo ≈ zero.** O Free Tier *sempre grátis* dá 25 GB de armazenamento e capacidade
  de sobra pro laboratório. Sem pressa nesta parte.
- **RDS: atenção.** O Free Tier (12 meses) dá **750h/mês** de `db.t3.micro`/`db.t4g.micro`
  Single-AZ + 20 GB. Dentro dele: US$ 0. **Fora do Free Tier**, um db.t3.micro custa ~US$ 0,017/h
  (~US$ 12+/mês) **enquanto existir**. Regras desta prática:
  - **NÃO habilite Multi-AZ** (dobra o custo e sai do Free Tier).
  - Faça a parte do RDS **numa sessão só** e **delete no teardown** — vamos usar
    `--skip-final-snapshot` e desligar a proteção de deleção.
  - Snapshot manual esquecido **também cobra storage**. Não deixaremos nenhum.
- Região: **`us-east-1`**.

---

# PARTE 1 — DynamoDB (protagonista)

## Parte A — Criar tabela (Console)

### Passo 1 — Tabela `pedidos`
1. Console → **DynamoDB** → **Tables** → **Create table**.
2. Nome: `pedidos` · **Partition key:** `cliente_id` (String) · **Sort key:** `data_pedido` (String).
3. Table settings: **Customize settings** → Capacity mode: **On-demand**. (Sem instância, sem AZ —
   repare como *não* há nada de infraestrutura pra decidir. Isso é serverless.)
4. Crie.

> **Por quê essas chaves:** nossa "pergunta principal" é *"pedidos de um cliente, por período"*.
> PK=`cliente_id` agrupa; SK=`data_pedido` (formato ISO `2026-07-18`) ordena e permite intervalo.
> No DynamoDB, **a tabela nasce do padrão de acesso**.

### Passo 2 — Inserir itens pelo Console
1. Tabela → **Explore table items** → **Create item**.
2. Crie um item: `cliente_id = "c001"`, `data_pedido = "2026-07-01"` e adicione (Add new attribute)
   `total` (Number) = `150` e `status` (String) = `"ENTREGUE"`.
3. Repare no formulário: **itens da mesma tabela podem ter atributos diferentes** — só as chaves
   são obrigatórias (schemaless).

## Parte B — CRUD pela CLI

```bash
# Mais itens (repare no formato de tipos do DynamoDB: S=string, N=number)
aws dynamodb put-item --table-name pedidos --item '{
  "cliente_id": {"S": "c001"}, "data_pedido": {"S": "2026-07-15"},
  "total": {"N": "89"}, "status": {"S": "CANCELADO"}}'

aws dynamodb put-item --table-name pedidos --item '{
  "cliente_id": {"S": "c001"}, "data_pedido": {"S": "2026-08-02"},
  "total": {"N": "320"}, "status": {"S": "ENTREGUE"}}'

aws dynamodb put-item --table-name pedidos --item '{
  "cliente_id": {"S": "c002"}, "data_pedido": {"S": "2026-07-10"},
  "total": {"N": "42"}, "status": {"S": "CANCELADO"}}'

# get-item: busca EXATA pela chave completa (PK+SK) — O(1)
aws dynamodb get-item --table-name pedidos --key '{
  "cliente_id": {"S": "c001"}, "data_pedido": {"S": "2026-07-15"}}'
```

### Passo 3 — Query: a busca certa
```bash
# Todos os pedidos do cliente c001
aws dynamodb query --table-name pedidos \
  --key-condition-expression "cliente_id = :c" \
  --expression-attribute-values '{":c": {"S": "c001"}}'

# Pedidos do c001 SÓ de julho (intervalo na sort key!)
aws dynamodb query --table-name pedidos \
  --key-condition-expression "cliente_id = :c AND data_pedido BETWEEN :ini AND :fim" \
  --expression-attribute-values '{":c": {"S": "c001"}, ":ini": {"S": "2026-07-01"}, ":fim": {"S": "2026-07-31"}}'
```

> A query foi **direto** à partição do `c001` e usou a ordenação da SK. Não importa se a tabela tem
> 4 itens ou 4 bilhões: o custo é proporcional **ao que ela retorna**.

### Passo 4 — Scan: a busca errada (de propósito)
```bash
# "Quero todos os pedidos CANCELADOS" — status NÃO é chave...
aws dynamodb scan --table-name pedidos \
  --filter-expression "#s = :st" \
  --expression-attribute-names '{"#s": "status"}' \
  --expression-attribute-values '{":st": {"S": "CANCELADO"}}' \
  --return-consumed-capacity TOTAL
```

Olhe o campo **`ScannedCount` vs. `Count`** na resposta: o DynamoDB **leu TODOS os itens** (4) pra
retornar 2. O filtro é aplicado **depois** da leitura — **você paga pelo lido, não pelo retornado**.
Agora imagine 10 GB de tabela: é por isso que **scan em produção é quase sempre erro de modelagem**.

## Parte C — GSI: transformando o scan em query

### Passo 5 — Criar o índice
```bash
aws dynamodb update-table --table-name pedidos \
  --attribute-definitions AttributeName=status,AttributeType=S AttributeName=data_pedido,AttributeType=S \
  --global-secondary-index-updates '[{"Create": {
      "IndexName": "status-data-index",
      "KeySchema": [
        {"AttributeName": "status", "KeyType": "HASH"},
        {"AttributeName": "data_pedido", "KeyType": "RANGE"}],
      "Projection": {"ProjectionType": "ALL"}}}]'

# Aguarde o índice ficar ACTIVE (~1 min)
aws dynamodb describe-table --table-name pedidos \
  --query "Table.GlobalSecondaryIndexes[].{Nome:IndexName,Status:IndexStatus}"
```

### Passo 6 — A mesma pergunta, agora barata
```bash
aws dynamodb query --table-name pedidos --index-name status-data-index \
  --key-condition-expression "#s = :st" \
  --expression-attribute-names '{"#s": "status"}' \
  --expression-attribute-values '{":st": {"S": "CANCELADO"}}' \
  --return-consumed-capacity TOTAL
```

Mesmo resultado do scan, mas via **query no GSI**: foi direto aos itens CANCELADO. `Count` ==
`ScannedCount`. Você acabou de fazer a otimização mais importante do DynamoDB: **acesso novo →
índice novo**, não scan.

---

# PARTE 2 — RDS MySQL (com teardown rigoroso)

> ⏰ Daqui até o fim do teardown, faça **sem pausas longas** — a instância existe e (fora do Free
> Tier) cobra por hora.

## Parte D — Criar a instância (Console)

### Passo 7 — Criar o banco
1. Console → **RDS** → **Create database** → **Standard create**.
2. Engine: **MySQL** (versão default). Template: **Free tier** ⭐ (isso já trava Single-AZ e
   classes elegíveis).
3. DB instance identifier: `m07-mysql` · Master username: `admin` · **Self managed password**:
   defina uma senha forte e **anote**.
4. Instance: `db.t3.micro` (ou `db.t4g.micro`). Storage: 20 GB gp3, **desmarque autoscaling**.
5. **Connectivity:** VPC default · **Public access: Yes** (⚠️ só pra este laboratório! Em produção,
   banco NUNCA é público — a app acessa por dentro da VPC) · VPC security group: **Create new** →
   `m07-rds-sg` (ele libera a porta 3306 só pro **seu IP atual**).
6. Em **Additional configuration**: Initial database name: `loja` · **desmarque** Enable automated
   backups (agiliza o lab; em produção, jamais) · desmarque Enhanced Monitoring.
7. Crie. Vai levar **5–10 min** até `Available`. Enquanto isso, explore as abas:
   - **Configuration**: veja a classe, Single-AZ, o **parameter group** (`default.mysql8...`).
   - **Maintenance & backups**: a **janela de manutenção** semanal.

### Passo 8 — Conectar de verdade
1. Na página da instância, copie o **Endpoint** (algo como
   `m07-mysql.xxxx.us-east-1.rds.amazonaws.com`).
2. Do seu terminal (instale um client se preciso: `sudo dnf install mariadb105` /
   `sudo apt install mysql-client`):

```bash
mysql -h SEU-ENDPOINT -u admin -p
```

3. Dentro do MySQL, prove que é um MySQL de verdade:

```sql
SHOW DATABASES;
USE loja;
CREATE TABLE produtos (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(100), preco DECIMAL(10,2));
INSERT INTO produtos (nome, preco) VALUES ('Teclado', 199.90), ('Mouse', 89.90);
SELECT * FROM produtos;
exit
```

> Sinta a diferença de modelo: aqui há **schema, SQL, JOINs possíveis** — e uma **instância** que
> existe (e custa) 24/7, com classe, storage e janela de manutenção. No DynamoDB, nada disso existia.

### Passo 9 — Inspecionar pela CLI
```bash
aws rds describe-db-instances --db-instance-identifier m07-mysql \
  --query "DBInstances[].{Status:DBInstanceStatus,Classe:DBInstanceClass,MultiAZ:MultiAZ,Endpoint:Endpoint.Address,Backup:BackupRetentionPeriod}"
```
> Repare: `MultiAZ: false` (Free Tier) e `Backup: 0` (desligamos). Em produção seria
> `MultiAZ: true` e retenção 7–35.

## Parte E — 🔥 TEARDOWN do RDS (obrigatório!)

```bash
# Deletar SEM snapshot final (laboratório!) — em produção seria o contrário
aws rds delete-db-instance \
  --db-instance-identifier m07-mysql \
  --skip-final-snapshot \
  --delete-automated-backups

# Acompanhar até a instância sumir (status 'deleting' → erro NotFound = sucesso)
aws rds describe-db-instances --db-instance-identifier m07-mysql \
  --query "DBInstances[].DBInstanceStatus"

# Conferir que NENHUM snapshot ficou pra trás (deve vir vazio)
aws rds describe-db-snapshots --query "DBSnapshots[].DBSnapshotIdentifier"

# Apagar o security group criado pro RDS (depois que a instância sumir)
aws ec2 delete-security-group --group-name m07-rds-sg
```

> ⚠️ **Os dois esquecimentos que custam dinheiro:** (1) a **instância** viva — cobra por hora após
> o Free Tier; (2) **snapshots** manuais/finais — cobram storage pra sempre. A verificação acima
> garante que nada ficou.

## Parte F — Teardown do DynamoDB (opcional)

A tabela `pedidos` com 4 itens custa ~nada (Free Tier sempre-grátis de 25 GB) — pode até deixar
pra brincar. Mas o ritual é o ritual:

```bash
aws dynamodb delete-table --table-name pedidos
aws dynamodb list-tables
```

---

## ✅ Checklist de conclusão do módulo

- [ ] Tabela `pedidos` criada (PK+SK) em modo on-demand — Console e entendimento do porquê das chaves.
- [ ] `put-item` / `get-item` feitos pela CLI (e o formato de tipos `{"S": ...}` entendido).
- [ ] `query` por PK e por intervalo de SK executadas.
- [ ] `scan` com filtro executado e **`ScannedCount` vs. `Count` interpretado** (por que scan é caro).
- [ ] GSI `status-data-index` criado e a mesma busca refeita como query barata.
- [ ] Instância RDS MySQL Free Tier criada; parameter group e janela de manutenção localizados.
- [ ] Conexão real via `mysql` + CREATE TABLE/INSERT/SELECT.
- [ ] **RDS deletado com `--skip-final-snapshot`** e verificação de zero snapshots restantes.
- [ ] Security group do RDS removido.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-07/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-07/`) e para o **Módulo 08 — Serverless**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 7" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
