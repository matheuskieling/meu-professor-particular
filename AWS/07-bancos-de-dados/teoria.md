# Módulo 07 — Bancos de dados (Teoria)

> Objetivo do módulo: dominar o cardápio de bancos gerenciados da AWS e — mais importante —
> saber **escolher**: **RDS** (relacional gerenciado, com a diferença crucial entre **Multi-AZ**
> e **read replicas**), **Aurora**, **DynamoDB** (NoSQL serverless, partition keys, índices) e
> **ElastiCache** (Redis/Memcached). No fim, você olha pra um requisito e sabe dizer qual banco
> faz sentido — que é o que separa quem "usa" de quem "arquiteta".

---

## 1. Por que banco **gerenciado**?

Você *pode* instalar um MySQL num EC2 (é IaaS, o SO é seu). Mas aí backup, patch, réplica,
failover, tuning de SO — tudo vira seu plantão. Um banco **gerenciado** (RDS & cia) inverte isso:
a AWS cuida da máquina, do motor, do backup e do failover; você cuida do **schema, das queries e
dos dados**. É o modelo de responsabilidade compartilhada aplicado a dados: pague um pouco mais
por instância, durma bem mais.

---

## 2. Amazon RDS — relacional gerenciado

**RDS (Relational Database Service)** roda os motores que você já conhece, gerenciados:
**MySQL, PostgreSQL, MariaDB, SQL Server, Oracle** (+ Aurora, seção 3). Você escolhe motor,
classe de instância (`db.t3.micro`, `db.r6g.large`…), storage, e a AWS opera.

### Multi-AZ vs. Read Replicas — a diferença crucial ⭐

Este é **o** ponto mais cobrado (em prova e na vida). Os dois criam "cópias", mas com propósitos
**opostos**:

| | **Multi-AZ** | **Read Replica** |
|---|---|---|
| Propósito | **Disponibilidade** (sobreviver a falha) | **Escala de leitura** (performance) |
| Replicação | **Síncrona** (standby sempre em dia) | **Assíncrona** (pode atrasar — *replication lag*) |
| A cópia recebe tráfego? | **Não** — standby invisível, só espera | **Sim** — leituras apontadas pra ela |
| Endpoint | **Um só**; no failover, o DNS passa a apontar pro standby (~1–2 min, automático) | **Cada réplica tem o seu**; a app decide pra onde mandar leituras |
| Onde | Outra AZ, mesma região | Mesma AZ, outra AZ ou **outra região** |
| Vira primário? | Automaticamente, no failover | Só se você **promover** manualmente (vira banco independente) |

**Memorize assim:** Multi-AZ é o **pneu estepe** (não roda no dia a dia, salva na emergência).
Read replica é um **carro extra na frota** (trabalha todo dia carregando leituras).

> ⚠️ **Armadilha clássica:** achar que Multi-AZ melhora performance. Não melhora **nada** — o
> standby não atende uma query sequer. E read replica **não** é solução de disponibilidade
> primária: a replicação assíncrona pode perder as últimas escritas. Dá pra (e é comum) usar
> **os dois juntos**.

### Backups: automáticos vs. snapshots manuais

| | **Backup automático** | **Snapshot manual** |
|---|---|---|
| Quem dispara | O RDS, diariamente (na janela de backup) + transaction logs | Você (ou um script seu) |
| Point-in-time restore | **Sim** — restaura pra qualquer segundo dentro da retenção (1–35 dias) | Não — restaura o momento do snapshot |
| Quando some | **Apagado junto** quando a instância é deletada (por padrão) | **Fica até você apagar** (e continua cobrando storage!) |

> 💡 Ao deletar uma instância RDS, a AWS oferece um **final snapshot**. Em produção: **sempre**.
> No laboratório: `--skip-final-snapshot` (senão o snapshot fica pra trás cobrando).

Restaurar **sempre cria uma instância nova** — não "volta no tempo" a existente.

### Parameter groups e janela de manutenção

- **Parameter group** — como você **não tem acesso ao SO/arquivos** do RDS, os parâmetros do motor
  (ex.: `max_connections`, timeouts) são editados via parameter group anexado à instância. Alguns
  parâmetros são dinâmicos; outros exigem reboot.
- **Maintenance window** — janela semanal em que a AWS aplica patches/upgrades. Escolha um horário
  de baixo tráfego. Com Multi-AZ, a manutenção usa o standby pra minimizar a indisponibilidade.

---

## 3. Aurora — o relacional "cloud-native" da AWS

**Aurora** é o motor da própria AWS, **compatível com MySQL e PostgreSQL** (mesmo protocolo — sua
app não muda), mas com a arquitetura reinventada pra nuvem:

- **Storage desacoplado do compute:** os dados vivem numa camada distribuída que mantém **6 cópias
  em 3 AZs**, crescendo automaticamente (até 128 TB+). As instâncias são "só" compute em cima.
- Até **15 réplicas** lendo **do mesmo storage** (lag mínimo), com **reader endpoint** que balanceia
  leituras entre elas.
- **Failover mais rápido** que o RDS clássico (tipicamente ~30s), promovendo uma réplica.
- Desempenho superior aos motores de origem no mesmo hardware (marketing diz 5x/3x; na prática,
  "mais rápido, especialmente sob concorrência").

### Aurora Serverless v2

Compute que **escala automaticamente e de forma fina** (em ACUs — frações de capacidade), pra cima
e pra baixo, conforme a carga. Ideal pra cargas **intermitentes ou imprevisíveis** (dev/test, SaaS
multi-tenant, picos raros): você paga pela capacidade consumida, não por uma instância parada.

**Quando Aurora em vez de RDS?** Precisa de mais performance, failover rápido, muitas réplicas ou
escala elástica → Aurora. Orçamento apertado, carga modesta, ou motor específico (SQL Server,
Oracle) → RDS clássico. (Aurora tende a custar mais que RDS pequeno.)

---

## 4. DynamoDB — NoSQL serverless

**DynamoDB** é o banco **chave-valor/documento** da AWS: **totalmente serverless** (sem instância,
sem patch, sem AZ pra escolher), latência de **milissegundos de um dígito** em qualquer escala,
replicado em 3 AZs automaticamente. Você cria a **tabela** e pronto.

### O modelo de dados: partition key (+ sort key)

- **Partition key (PK)** — obrigatória. O hash dela decide **onde** o item fica. Buscar por PK é
  O(1): rápido e barato **sempre**.
- **Sort key (SK)** — opcional. Itens com a mesma PK ficam **ordenados** pela SK, permitindo
  queries de intervalo: "pedidos do cliente X **entre janeiro e março**".
- A chave primária = PK (ou PK+SK). **Todo o design da tabela gira em torno de: "quais perguntas
  vou fazer?"** — no DynamoDB você modela pelos **padrões de acesso**, não pela 3ª forma normal.

### Query vs. Scan — por que Scan é caro ⚠️

- **Query** — usa a PK (e opcionalmente condições na SK). Vai **direto** à partição certa. Eficiente.
- **Scan** — **lê a tabela inteira**, item por item, filtrando depois. Custa capacidade de leitura
  proporcional a **tudo que leu**, não ao que retornou. Numa tabela grande: lento, caro e capaz de
  estrangular a capacidade provisionada. **Scan em produção é quase sempre um erro de modelagem.**

### Índices secundários: GSI e LSI

E quando você precisa buscar por **outro atributo** que não a PK?

| | **GSI** (Global Secondary Index) | **LSI** (Local Secondary Index) |
|---|---|---|
| O que muda | **PK e SK completamente novas** | Mesma PK, **outra SK** |
| Quando criar | **A qualquer momento** | **Só na criação da tabela** |
| Capacidade | Própria (ou on-demand) | Compartilhada com a tabela |
| Consistência | Eventual | Pode ser forte |

Na prática, **GSI resolve 95% dos casos**: "buscar pedidos por status", "usuários por e-mail".
É como criar uma "visão reordenada" da tabela, mantida automaticamente.

### Capacidade: on-demand vs. provisionada

- **On-demand** — paga **por requisição** (RCU/WCU consumidas). Zero planejamento, escala
  instantânea. Ideal pra começar, pra cargas imprevisíveis e pra laboratório.
- **Provisionada** — você reserva X leituras/s e Y escritas/s (mais barato em carga **estável e
  previsível**; pode ter auto scaling). Estourou a capacidade → *throttling* (`ProvisionedThroughputExceededException`).

### TTL e outros recursos

- **TTL** — um atributo com timestamp; o item **expira e é deletado de graça** depois dele. Perfeito
  pra sessões, caches, dados temporários.
- Extras que valem conhecer de nome: **Streams** (fluxo de mudanças → dispara Lambda), **DAX**
  (cache em microssegundos na frente da tabela), **Global Tables** (multi-região ativa-ativa).

### Quando NoSQL (DynamoDB) faz sentido?

✅ Padrões de acesso **conhecidos e simples** (busca por chave), escala massiva, latência
constante, serverless, sessões/carrinhos/perfis/IoT/eventos.
❌ Queries **ad-hoc e relatórios** (JOIN, agregações livres), transações complexas multi-tabela,
requisitos que mudam de pergunta toda semana → relacional.

---

## 5. ElastiCache — o cache na frente do banco

**ElastiCache** oferece **Redis** (rico: estruturas de dados, persistência opcional, pub/sub,
replicação/failover — o padrão de mercado) e **Memcached** (mais simples, multi-thread, cache puro).
Na dúvida: **Redis**.

### Padrão cache-aside (o que você vai usar 90% das vezes)

```
1. App precisa do dado → pergunta AO CACHE primeiro.
2. Cache HIT  → responde em microssegundos. Fim.
3. Cache MISS → busca no banco → responde → GRAVA no cache com TTL.
   Próxima requisição igual: HIT.
```

Efeito: leituras repetidas saem do banco caro/lento e vão pro cache barato/rápido. É a primeira
arma contra banco relacional sobrecarregado de leitura (antes até de read replicas).

> ⚠️ **Armadilhas do cache:** dado **desatualizado** (invalidar/expirar com TTL sensato) e
> **cold start** (cache vazio após restart = avalanche no banco). Cache é otimização, não fonte
> de verdade.

---

## 6. Comparativo final — qual banco escolher?

| Requisito | Escolha | Por quê |
|-----------|---------|---------|
| CRUD relacional clássico, SQL, JOINs, relatórios | **RDS** | Motores conhecidos, gerenciado, barato pra começar |
| Relacional com alta performance/escala, failover rápido | **Aurora** | Storage 6 cópias/3 AZs, 15 réplicas, ~30s failover |
| Relacional com carga intermitente/imprevisível | **Aurora Serverless v2** | Capacidade acompanha a carga, paga o que usa |
| Chave-valor massivo, latência constante, serverless | **DynamoDB** | Sem servidor, ms de um dígito em qualquer escala |
| Sessões, carrinho, contador, leaderboard, dados com TTL | **DynamoDB** (ou Redis) | Acesso por chave + TTL nativo |
| Acelerar leituras repetidas / aliviar o banco | **ElastiCache (Redis)** | Cache-aside, microssegundos |
| Analytics/BI pesado (colunar, petabytes) | Redshift* | *Fora do escopo deste módulo — só saiba que existe |

**Pergunta-guia:** *"Como meus dados serão acessados?"* — não "qual banco é mais moderno".
Acesso relacional/ad-hoc → SQL. Acesso por chave em escala → DynamoDB. Leitura repetida → cache.

---

## 7. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| RDS | Bancos relacionais clássicos, gerenciados pela AWS. |
| Multi-AZ | Standby síncrono e invisível em outra AZ; failover automático — **disponibilidade**. |
| Read replica | Cópia assíncrona com endpoint próprio pra leituras — **performance**. |
| Backup automático | Diário + logs; permite point-in-time restore; some com a instância. |
| Snapshot manual | Backup disparado por você; fica (e cobra) até você apagar. |
| Parameter group | Onde se ajustam os parâmetros do motor (você não tem acesso ao SO). |
| Aurora | Relacional cloud-native da AWS: storage 6 cópias/3 AZs, compatível MySQL/PostgreSQL. |
| Aurora Serverless v2 | Compute do Aurora escalando fino (ACUs) conforme a carga. |
| Partition key / sort key | Decide a partição do item / ordena itens dentro da partição. |
| Query vs. Scan | Direto na partição vs. ler a tabela inteira (caro — evite). |
| GSI / LSI | Índice com PK+SK novas, criável sempre / mesma PK, outra SK, só na criação. |
| On-demand vs. provisionada | Paga por requisição vs. reserva capacidade (throttling se estourar). |
| TTL | Item expira e é deletado automaticamente, de graça. |
| Cache-aside | Padrão: tenta o cache; miss → banco → grava no cache com TTL. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Multi-AZ e read replica: qual serve pra **disponibilidade** e qual pra **performance**? Por que
   a replicação síncrona vs. assíncrona é a chave dessa diferença?
2. Você deletou uma instância RDS com `--skip-final-snapshot`. O que aconteceu com os backups
   automáticos? E com os snapshots manuais?
3. No DynamoDB, por que um **Scan** numa tabela de 10 GB é um problema, e o que um **GSI** resolve?
4. Sua tabela é `pedidos` com PK=`cliente_id`, SK=`data`. Como você buscaria "pedidos do cliente
   123 em junho"? E "todos os pedidos com status=CANCELADO" — o que falta?
5. Em que ordem você atacaria um banco relacional sobrecarregado de **leituras**: read replica,
   cache, instância maior? Justifique.

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
