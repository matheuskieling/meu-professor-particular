# Módulo 17 — Otimização de Custos (FinOps) (Teoria)

> Objetivo do módulo: transformar você de "pagador de fatura" em **operador de custos**. Você vai
> entender a cultura **FinOps**, aprender a **ler a fatura** de verdade (Cost Explorer, CUR, tags),
> dominar os **modelos de compra** (On-Demand, Savings Plans, Reserved, Spot), fazer **right-sizing**
> e caçar os **vilões clássicos de custo** que sangram contas em silêncio. Ao final, custo deixa de
> ser surpresa e vira uma métrica de engenharia como qualquer outra.

---

## 1. FinOps: custo é problema de engenharia, não só do financeiro

**FinOps** (Finance + DevOps) é a prática cultural de fazer engenharia, finanças e negócio
trabalharem juntos sobre o custo de nuvem. A ideia central: na nuvem, **quem cria o custo é quem
faz o deploy** — cada `terraform apply` é uma decisão financeira. Então a responsabilidade pelo
gasto migra do departamento financeiro para o time de engenharia.

O ciclo FinOps tem três fases, que se repetem continuamente:

| Fase | Pergunta que responde | Ferramentas típicas |
|------|----------------------|---------------------|
| **1. Visibilidade (Inform)** | "Pra onde está indo o dinheiro?" | Cost Explorer, CUR, tags, dashboards |
| **2. Otimização (Optimize)** | "Onde dá pra gastar menos sem perder valor?" | Right-sizing, Savings Plans, Spot, lifecycle |
| **3. Operação (Operate)** | "Como manter isso sob controle sempre?" | Budgets, Anomaly Detection, revisões periódicas |

> 💡 **Regra mental:** não dá pra otimizar o que você não enxerga. Por isso a ordem importa:
> **visibilidade primeiro**, otimização depois, e operação contínua pra não regredir. Pular direto
> pra "comprar Savings Plan" sem visibilidade é como fazer dieta sem balança.

Um princípio clássico de FinOps: **unit economics** — não olhe só o custo absoluto ("gastamos
US$ 10 mil"), olhe o custo **por unidade de valor** ("gastamos US$ 0,002 por pedido processado").
Custo subindo com receita subindo mais rápido pode ser ótimo; custo estável com uso caindo é ruim.

---

## 2. Entendendo a fatura: Billing, Cost Explorer e CUR

Três níveis de profundidade para olhar o mesmo gasto:

### Billing and Cost Management (a fatura)
O console de **Billing** mostra a fatura consolidada: quanto você deve neste mês, por serviço.
É o extrato. Bom pra conferência, ruim pra investigação.

### Cost Explorer (a lupa)
O **Cost Explorer** é a ferramenta interativa de análise: gráficos de custo/uso ao longo do tempo,
com **filtros** e **agrupamentos** (por serviço, por região, por tag, por conta, por tipo de
compra...). É aqui que você responde perguntas como "por que outubro custou 30% a mais?".

- Precisa ser **habilitado** uma vez (leva até 24h pra popular os dados).
- A interface é **gratuita**; a API paga por requisição (~US$ 0,01/chamada).
- Guarda ~13 meses de histórico e faz previsão (forecast) dos próximos meses.
- Tem relatórios prontos úteis: *Monthly costs by service*, cobertura/utilização de RI e Savings Plans.

### Cost and Usage Report — CUR (o microscópio)
O **CUR** (hoje evoluído para **Data Exports / CUR 2.0**) é o dado **bruto e completo**: cada
linha de cobrança, hora a hora, recurso a recurso, entregue em arquivos no **S3**. É o que
empresas usam pra alimentar Athena/QuickSight e ferramentas de FinOps. Você não vai precisar dele
no dia a dia deste curso, mas precisa saber: **quando o Cost Explorer não responde, o CUR responde**
— ele é a fonte de verdade da qual tudo deriva.

| Ferramenta | Granularidade | Uso típico |
|------------|---------------|-----------|
| Billing | Mensal, por serviço | "Quanto devo?" |
| Cost Explorer | Diária/mensal, filtros e grupos | "Onde e por que gastei?" |
| CUR / Data Exports | Por hora, por recurso, cada linha | Análise profunda, BI, ferramentas FinOps |

---

## 3. Tags de alocação de custo (cost allocation tags)

Você já usa **tags** desde os primeiros módulos (`Name`, `Projeto`...). Mas tag comum **não aparece
na fatura** automaticamente. Para uma tag virar dimensão de custo, você precisa **ativá-la como
cost allocation tag** no console de Billing.

Dois tipos:
- **AWS-generated** (ex.: `aws:createdBy`) — a AWS preenche sozinha.
- **User-defined** (ex.: `Projeto`, `Ambiente`, `Time`, `CentroDeCusto`) — as suas.

Pontos que pegam todo mundo:
- A ativação **não é retroativa**: só marca o custo **dali pra frente** (e leva até 24h pra aparecer).
- Recurso **sem tag** vira um balde de "sem alocação" — o buraco negro da fatura.
- Tag é **case-sensitive**: `projeto`, `Projeto` e `PROJETO` são três tags diferentes na fatura. 😱

### Estratégia de tagging (o que times maduros fazem)
1. **Defina um dicionário mínimo obrigatório** — ex.: `Projeto`, `Ambiente` (`dev`/`prod`), `Owner`.
2. **Padronize grafia** (decida `Ambiente=prod`, e ninguém escreve `Producao`).
3. **Aplique via IaC** — tags no código (como `default_tags` no Terraform) não dependem de disciplina humana.
4. **Fiscalize** — AWS Config e Tag Policies (Organizations) podem detectar/bloquear recurso sem tag.

> 🎯 Com tags ativadas, o Cost Explorer responde "quanto custa o projeto X no ambiente dev?" —
> sem elas, você só sabe "quanto custa o EC2", o que não ajuda ninguém a decidir nada.

---

## 4. Right-sizing: pagar pelo tamanho certo

**Right-sizing** = ajustar o tamanho do recurso ao uso real. O desperdício clássico: uma
`m5.xlarge` (4 vCPU, 16 GB) rodando com 5% de CPU — você paga 4x o que uma `m5.large` custaria
ou mais, por capacidade que nunca usa.

Como decidir com dados, não com achismo:
- **CloudWatch** (Módulo 12): olhe `CPUUtilization`, rede, e — com o agent — memória, num período
  representativo (14+ dias, incluindo picos).
- **AWS Compute Optimizer**: serviço **gratuito** que analisa as métricas dos últimos 14 dias e
  recomenda: *over-provisioned* (diminua), *under-provisioned* (aumente) ou *optimized*. Cobre
  EC2, ASGs, volumes EBS, funções Lambda e ECS/Fargate. Precisa ser habilitado (opt-in) e ter
  histórico mínimo de métricas para gerar recomendação.

Regras práticas:
- Diminuir um "degrau" de instância ≈ **~50% de economia** naquela instância. É a otimização de
  melhor custo-benefício que existe.
- Cuidado com métricas que o CloudWatch **não vê por padrão** (memória!) — instale o agent antes
  de encolher uma instância que pode estar limitada por RAM.
- Right-sizing vem **antes** de comprar Savings Plans/RIs: reservar capacidade superdimensionada
  é travar o desperdício por 1–3 anos.

---

## 5. Modelos de compra: On-Demand, Savings Plans, Reserved, Spot

A mesma instância EC2 pode custar 4 preços muito diferentes conforme **como** você compra:

| Modelo | Desconto típico | Compromisso | Melhor para |
|--------|-----------------|-------------|-------------|
| **On-Demand** | 0% (referência) | Nenhum | Testes, picos, cargas imprevisíveis |
| **Savings Plans** | até ~66–72% | US$/hora por 1 ou 3 anos | Uso estável de compute |
| **Reserved Instances** | até ~72% | Instância específica, 1 ou 3 anos | Uso estável e previsível (ex.: RDS) |
| **Spot** | até ~90% | Nenhum, mas pode ser interrompida | Cargas tolerantes a interrupção |

### Savings Plans (o jeito moderno de reservar)
Você se compromete a gastar **X dólares/hora** de compute por 1 ou 3 anos; tudo que couber nesse
compromisso sai com desconto, e o excedente vai a preço On-Demand. Dois sabores:

- **Compute Savings Plans** — o mais **flexível**: vale para **qualquer** família de instância,
  qualquer região, e também **Fargate e Lambda**. Desconto de até ~66%.
- **EC2 Instance Savings Plans** — preso a uma **família de instância numa região** (ex.: `m5`
  em `us-east-1`), mas dentro dela troca tamanho/SO/AZ à vontade. Desconto maior, até ~72%.

> Regra mental: **flexibilidade e desconto são trocados um pelo outro.** Quanto mais você
> se amarra, mais barato fica.

### Reserved Instances (RIs)
O modelo mais antigo: você reserva **uma configuração de instância** (tipo, região, plataforma)
por 1 ou 3 anos. *Standard* (desconto máximo, pouca troca) ou *Convertible* (menor desconto, pode
trocar de família). Para **EC2**, Savings Plans praticamente substituíram as RIs — mas RIs
continuam sendo **o** mecanismo de reserva para **RDS, ElastiCache, OpenSearch, Redshift**
(Savings Plans não cobrem bancos!).

Em todos os casos de reserva, paga-se menos ainda com adiantamento: *No Upfront* < *Partial
Upfront* < *All Upfront* (tudo antecipado = maior desconto).

### Spot Instances
A AWS vende a **capacidade ociosa** com desconto de até 90%. O acordo: a AWS pode **retomar a
instância quando precisar**, com um aviso de **2 minutos** (a *interruption notice*, entregue via
metadados da instância e evento no EventBridge). Sua aplicação tem 2 minutos para salvar estado e
sair graciosamente.

- **Ótimo para:** processamento em lote, CI/CD, renderização, big data, workers de fila (SQS!),
  parte de um ASG (misturando On-Demand + Spot).
- **Péssimo para:** bancos de dados, aplicações com estado que não toleram morrer sem aviso.
- Boas práticas: **diversifique tipos de instância e AZs** (menos chance de interrupção em massa)
  e trate a interrupção como evento normal, não como falha.

> 💡 Estratégia madura de portfólio: uma **base estável** coberta por Savings Plans + **picos** em
> On-Demand + **cargas tolerantes** em Spot. Não é um-ou-outro; é a mistura.

---

## 6. Otimizando storage

Storage parece barato até acumular. Três otimizações de alto impacto:

1. **Lifecycle no S3** (Módulo 06 revisitado): dados esfriam com o tempo. Regras de lifecycle
   movem objetos para classes mais baratas (Standard → Standard-IA → Glacier) e **expiram** o que
   não precisa viver pra sempre. Não sabe o padrão de acesso? **S3 Intelligent-Tiering** decide
   por objeto, automaticamente. E não esqueça: regra pra **abortar multipart uploads incompletos**
   (lixo invisível que cobra).
2. **gp2 → gp3 no EBS**: gp3 é **~20% mais barato** que gp2 e com performance base **garantida**
   (3.000 IOPS / 125 MB/s) independente do tamanho. A migração é um clique/comando, **sem downtime**.
   Se você ainda tem volumes gp2, está pagando mais por menos.
3. **Snapshots órfãos**: snapshots de volumes/AMIs que já foram deletados continuam cobrando por
   GB-mês, para sempre, até alguém apagar. Contas antigas acumulam **anos** de snapshots que
   ninguém sabe de quê são. Na prática vamos caçá-los via CLI.

---

## 7. Os vilões clássicos de custo (a lista negra)

Memorize esta lista — ela paga o curso:

| Vilão | Por que sangra | Antídoto |
|-------|----------------|----------|
| **NAT Gateway** | ~US$ 0,045/h (~US$ 32/mês) **+ ~US$ 0,045/GB processado**, por AZ | Precisa mesmo? Endpoints de VPC pra S3/DynamoDB são grátis; em dev, considere desligar |
| **Transferência entre AZs** | ~US$ 0,01/GB **em cada direção** — invisível até a fatura chegar | Mantenha tráfego pesado na mesma AZ quando fizer sentido; meça antes |
| **IPv4 público** | Desde 2024, **~US$ 0,005/h por IP público** (~US$ 3,60/mês) — associado ou não | Libere Elastic IPs ociosos; use IPv6/private onde puder |
| **Logs sem retenção** | CloudWatch Logs com retenção "Never expire" cresce pra sempre (US$/GB armazenado) | Defina retenção (ex.: 30–90 dias) em **todo** log group |
| **Recursos zumbis** | Volumes EBS `available`, snapshots órfãos, EIPs soltos, load balancers sem alvo, EC2 parado com disco enorme | Caça periódica via CLI/scripts (faremos na prática) |
| **Data transfer OUT** | Saída pra internet cobra (~US$ 0,09/GB nos primeiros TB) | CloudFront na frente, compressão, cache |

> ⚠️ O padrão comum: **custo por existência, não por uso**. Esses recursos cobram enquanto
> existem, mesmo parados. Daí o teardown religioso que praticamos desde o Módulo 01.

---

## 8. Operação contínua: Budgets avançado e Anomaly Detection

### AWS Budgets além do básico
Você criou um budget simples no Módulo 01. O Budgets vai além:
- **Escopo por filtro**: budget **por serviço** ("EC2 não passa de US$ 5"), **por tag**
  ("projeto X não passa de US$ 20"), por conta, por região.
- **Alertas em limiares** múltiplos: 50%, 80%, 100% — do gasto **real** ou **previsto** (forecast:
  avisa que *vai* estourar antes de estourar).
- **Budget Actions**: além de avisar, o budget pode **agir** — aplicar uma política IAM restritiva,
  ou **parar instâncias EC2/RDS** quando o limite estoura. (Alertas são gratuitos; budgets com
  actions têm cota gratuita e depois custo pequeno por dia.)

### Cost Anomaly Detection
Budget pega o que você **previu**; anomalia pega o que você **não previu**. O **Cost Anomaly
Detection** usa machine learning para aprender o padrão de gasto da conta e alertar quando algo
**foge do padrão** (ex.: um serviço que custava centavos/dia pula pra dólares/hora). É
**gratuito**, e você configura monitores (por serviço é o mais comum) + assinaturas de alerta
(e-mail/SNS) com limiar mínimo. É a sua rede contra o "esqueci um recurso ligado" e contra
surpresas tipo credencial vazada minerando cripto na sua conta.

> 🎯 As três camadas de defesa, juntas: **Budgets** (limites que você define) +
> **Anomaly Detection** (desvios que você não previu) + **revisão periódica no Cost Explorer**
> (a fase "Operate" do FinOps). Nenhuma sozinha basta.

---

## 9. Estimando antes de construir: Pricing Calculator

Otimizar depois é bom; **estimar antes** é melhor. O **AWS Pricing Calculator**
(<https://calculator.aws>) monta estimativas de arquiteturas inteiras: você adiciona serviços,
configura (tipo de instância, horas/mês, GB, tráfego...) e ele gera o custo mensal — exportável
e compartilhável por link. Na prática, vamos estimar a arquitetura de referência do Módulo 15
(ALB + ASG + RDS Multi-AZ + S3/CloudFront) e comparar cenários On-Demand vs. Savings Plans.

---

## 10. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| FinOps | Cultura de tratar custo de nuvem como responsabilidade de engenharia, em ciclo contínuo. |
| Cost Explorer | Análise interativa de custo com filtros e agrupamentos (por serviço, tag...). |
| CUR / Data Exports | O dado bruto e completo da fatura, linha a linha, entregue no S3. |
| Cost allocation tag | Tag ativada no Billing que vira dimensão de análise na fatura (não retroativa). |
| Right-sizing | Ajustar o tamanho do recurso ao uso real medido. |
| Compute Optimizer | Serviço gratuito que recomenda right-sizing baseado em métricas. |
| Savings Plans | Compromisso de US$/h por 1–3 anos em troca de desconto (Compute ou EC2 Instance). |
| Reserved Instance | Reserva de configuração específica; ainda essencial para RDS e afins. |
| Spot | Capacidade ociosa com até 90% off; interrupção com aviso de 2 minutos. |
| Budget Action | Budget que age (política IAM, parar instâncias) ao estourar o limite. |
| Cost Anomaly Detection | ML que alerta gastos fora do padrão histórico. Gratuito. |
| Recurso zumbi | Recurso que ninguém usa mas continua cobrando (volume solto, EIP, snapshot órfão). |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Quais são as **três fases** do ciclo FinOps, e por que visibilidade vem primeiro?
2. Qual a diferença de propósito entre **Cost Explorer** e **CUR**?
3. Por que ativar uma cost allocation tag hoje **não** explica a fatura do mês passado?
4. **Compute Savings Plan** vs. **EC2 Instance Savings Plan**: o que você ganha e perde em cada um?
5. Sua carga roda workers consumindo uma fila SQS. Por que ela é candidata perfeita a **Spot**,
   e o que sua aplicação deve fazer ao receber o aviso de 2 minutos?
6. Cite **três vilões** de custo que cobram "por existir" e o antídoto de cada um.
7. Budget e Anomaly Detection não são redundantes — qual pega o quê?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
