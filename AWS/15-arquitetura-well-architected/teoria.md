# Módulo 15 — Arquitetura & Well-Architected (Teoria)

> Objetivo do módulo: sair do "sei usar cada serviço" para o "**sei desenhar sistemas**". Este é o
> módulo que **amarra tudo** que o curso viu: você vai aprender o **Well-Architected Framework**
> (a régua oficial da AWS pra avaliar arquiteturas), os **padrões** de arquitetura mais usados,
> os **anti-padrões** que derrubam sistemas, e vai montar mentalmente o desenho de referência de
> uma aplicação web resiliente — peça por peça, com os serviços que você já domina.

---

## 1. O que é "arquitetar" (e por que não existe resposta única)

Arquitetura é a arte de **escolher trade-offs conscientemente**. Todo desenho troca alguma coisa
por outra:

- Mais **disponibilidade** → mais redundância → mais **custo**.
- Mais **consistência** de dados → mais latência (ou menos disponibilidade).
- Mais **flexibilidade** (microservices) → mais **complexidade operacional**.
- Menos **operação** (serverless) → menos **controle fino**.

> 💡 A resposta de arquiteto pra quase tudo é **"depende — depende dos requisitos"**. A habilidade
> real é perguntar: *qual o SLA? qual o orçamento? qual o RTO/RPO? quantos usuários? qual o pico?*
> Requisitos primeiro, serviços depois. Quem começa escolhendo serviço está fazendo de trás pra frente.

---

## 2. O Well-Architected Framework

O **AWS Well-Architected Framework** é o conjunto de boas práticas que a AWS destilou de milhares
de arquiteturas reais. Ele organiza a avaliação de qualquer workload em **6 pilares** — e existe
uma ferramenta gratuita no console (**Well-Architected Tool**) que guia a revisão por perguntas.

### Os 6 pilares

| Pilar | Pergunta central | Exemplos de prática |
|-------|------------------|---------------------|
| **Excelência operacional** | "Conseguimos operar, evoluir e aprender com o sistema?" | IaC, deploys pequenos e reversíveis, runbooks, post-mortems sem culpados |
| **Segurança** | "Os dados e sistemas estão protegidos?" | Least privilege (IAM), criptografia em trânsito/repouso, rastreabilidade (CloudTrail), defesa em camadas |
| **Confiabilidade** | "O sistema se recupera de falhas e atende a demanda?" | Multi-AZ, auto scaling, health checks, backups testados, limites conhecidos |
| **Eficiência de performance** | "Usamos os recursos certos, do jeito certo?" | Tipos certos de instância/banco, serverless quando couber, cache (CloudFront/ElastiCache), medir sempre |
| **Otimização de custos** | "Gastamos só o necessário?" | Right-sizing, desligar o ocioso, Savings Plans/Spot, tags e visibilidade de gasto |
| **Sustentabilidade** | "Minimizamos o impacto ambiental?" | Menos recursos ociosos, regiões eficientes, serviços gerenciados, dados com lifecycle |

### Princípios-chave por pilar (o que cai em prova e na vida)

- **Excelência operacional:** *tudo como código*; mudanças **pequenas, frequentes e reversíveis**;
  antecipe falhas (game days); aprenda com incidentes.
- **Segurança:** identidade forte e **least privilege**; **rastreabilidade** (logs/auditoria);
  segurança **em todas as camadas** (edge, VPC, subnet, SG, app, dados); proteja dados em trânsito
  e em repouso; **automatize** as boas práticas; prepare-se pra incidentes.
- **Confiabilidade:** **recupere-se automaticamente** de falhas; **teste** os procedimentos de
  recuperação; **escale horizontalmente** (muitas máquinas pequenas > uma gigante); **pare de
  adivinhar capacidade** (auto scaling); gerencie mudanças por automação.
- **Performance:** **democratize tecnologias avançadas** (use serviços gerenciados em vez de operar
  você mesmo); vá **global em minutos** (CloudFront, multi-região); use **serverless** quando fizer
  sentido; **experimente** com frequência; conheça e meça (*mechanical sympathy*).
- **Custos:** implemente **cloud FinOps** (consciência de custo); meça a eficiência; **pare de
  gastar com datacenter**; **analise e atribua** os gastos (tags!); use o modelo de consumo (pague
  só o que usar — desligue o resto).
- **Sustentabilidade:** entenda seu impacto; **maximize a utilização** (recurso ocioso = desperdício
  duplo); adote hardware/serviços mais eficientes; reduza dados armazenados sem uso.

> ⚠️ **Armadilha de prova:** os pilares **conflitam** entre si de propósito. "Máxima confiabilidade"
> briga com "mínimo custo". A pergunta certa nunca é "qual o melhor pilar" — é **qual o requisito
> prioritário deste workload**. Um site interno de RH não precisa (nem deve pagar por) 99,99%.

---

## 3. Padrões de arquitetura

### 3.1 Multi-tier clássico (3 camadas)

O pão-com-manteiga: **apresentação → aplicação → dados**, cada camada numa subnet própria:

```
Internet → CloudFront/Route 53
   → [subnet pública]  ALB
   → [subnet privada]  EC2 em Auto Scaling Group (app)
   → [subnet privada]  RDS Multi-AZ (dados)
```

- Cada camada **escala e falha separadamente**; security groups encadeados (ALB → app → banco).
- É a arquitetura dos módulos 03–07 combinados. Simples de entender, madura, previsível.

### 3.2 Serverless

Sem servidores pra gerenciar; escala a zero (e a milhares):

```
Route 53 → CloudFront → S3 (front estático)
                      → API Gateway → Lambda → DynamoDB
```

- Paga **por requisição**; ótimo pra cargas variáveis/imprevisíveis ou baixas.
- Trade-off: cold starts, limites de execução (15 min), lock-in maior, debug diferente.

### 3.3 Event-driven (orientada a eventos)

Componentes **desacoplados** que se comunicam por eventos/mensagens (módulo 10):

```
Produtor → EventBridge/SNS/SQS → Consumidores independentes
```

- Quem produz **não conhece** quem consome; cada parte escala e falha sozinha.
- SQS dá **buffer** (absorve picos, retry, DLQ); SNS/EventBridge dão **fan-out** (1 evento → N reações).
- Trade-off: consistência **eventual**, rastreamento mais difícil (por isso X-Ray/correlação).

### 3.4 Microservices vs. monolito

| | Monolito | Microservices |
|---|---|---|
| Deploy | Um artefato, tudo junto | Independente por serviço |
| Escala | Tudo junto (mesmo o que não precisa) | Só o serviço sob demanda |
| Times | Um código, coordenação constante | Autonomia por serviço/time |
| Complexidade | No código (acoplamento interno) | Na **operação** (rede, observabilidade, versões) |
| Quando | Times pequenos, produto novo, requisitos voláteis | Escala grande, times múltiplos, domínios claros |

> 💡 **Anti-hype:** monolito **não** é anti-padrão. Um **monolito bem modularizado** num ASG atrás
> de um ALB é a escolha certa pra muita empresa. O anti-padrão é o *monolito distribuído*:
> microservices tão acoplados que precisam ser deployados juntos — a complexidade dos dois mundos,
> os benefícios de nenhum.

---

## 4. O desenho de referência — uma web app resiliente (amarrando o curso)

Este desenho junta **tudo** que você viu. Leia cada linha lembrando do módulo correspondente:

```
                        Route 53 (M14: DNS, alias, health checks)
                            │
                        CloudFront + ACM us-east-1 (M14: CDN, TLS)
                        │            │
              S3 privado c/ OAC    ALB (M05) + WAF (M13)
              (M06: front estático)  │        [subnets públicas, 2+ AZs]
                                     │
                            Auto Scaling Group (M05)
                            EC2 (M04) │ [subnets privadas, 2+ AZs]
                            IAM roles (M02) · SGs encadeados (M03)
                                     │
                    ┌────────────────┼────────────────┐
              RDS Multi-AZ (M07)  ElastiCache (M07)  SQS (M10: async)
              [subnets privadas]                       → workers/Lambda (M08)
                                     
  Transversais: CloudWatch + alarmes (M12) · CloudTrail (M12) · KMS (M13)
                IaC pra tudo (M11) · Budgets/tags (M01/M17)
```

Por que cada peça existe (a lógica, não a decoreba):

1. **2+ AZs em todas as camadas** — confiabilidade: uma AZ pode morrer inteira.
2. **ALB + ASG** — para de adivinhar capacidade; instância doente é substituída sozinha.
3. **RDS Multi-AZ** — failover automático do banco; réplicas de leitura se a leitura apertar.
4. **S3 + CloudFront pro estático** — tira carga dos servidores e entrega global; app serve só o dinâmico.
5. **Cache (ElastiCache)** — a requisição mais barata é a que não chega no banco.
6. **SQS pro trabalho assíncrono** — picos viram fila, não viram queda.
7. **Subnets privadas + SGs encadeados + least privilege** — segurança em camadas.
8. **CloudWatch/CloudTrail/alarmes** — você não conserta o que não vê.
9. **Tudo em IaC** — reproduzível, versionado, revisável; ambiente de teste idêntico ao de prod.

---

## 5. Anti-padrões comuns (o museu dos horrores)

- **AZ única** — "economizar" redundância; a primeira manutenção da AWS derruba o sistema.
- **Instância-estimação (pet)** — servidor único, configurado à mão, sem IaC, que "ninguém pode
  reiniciar". Trate servidores como **gado, não pets**: substituíveis por automação.
- **Banco na subnet pública / SG 0.0.0.0/0** — convite a incidente; camadas de dados nunca são públicas.
- **Escala vertical infinita** — resolver tudo aumentando a instância; um dia acaba o tamanho (e o teto de falha é total).
- **Acoplamento síncrono em cadeia** — A chama B que chama C…; a latência soma e a falha propaga.
  Onde puder, **fila no meio**.
- **Sem teste de recuperação** — backup que nunca foi restaurado **não é backup**, é esperança.
- **Monolito distribuído** — microservices acoplados com deploy conjunto (ver 3.4).
- **Otimização prematura** — arquitetura pra 10 milhões de usuários num produto com 10. Comece
  simples, evolua com dados.

---

## 6. Well-Architected Tool

No console (busque **AWS Well-Architected Tool**), **gratuito**:

1. Você define um **workload** (nome, descrição, ambiente, regiões).
2. Responde as **perguntas** de cada pilar (checkboxes de práticas que você segue).
3. A ferramenta aponta **HRIs/MRIs** (High/Medium Risk Issues) — riscos alto/médios — e gera um
   **plano de melhoria** priorizado com links pra documentação.
4. Você tira **milestones** (fotos no tempo) e mede a evolução da arquitetura entre revisões.

> 💡 Na prática das empresas, a revisão Well-Architected é um ritual periódico (ex.: semestral) ou
> pré-lançamento. Não é prova com nota: é um **espelho** — o valor está na conversa que as perguntas
> provocam no time. Na nossa prática, você vai rodar uma revisão de verdade no pilar de confiabilidade.

---

## 7. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Well-Architected Framework | As boas práticas da AWS organizadas em 6 pilares. |
| Trade-off | Toda decisão de arquitetura troca algo por algo; não existe grátis. |
| Multi-tier | Camadas de apresentação/app/dados, isoladas e escaláveis separadamente. |
| Serverless | Sem servidor pra operar; paga por uso; escala a zero. |
| Event-driven | Componentes desacoplados reagindo a eventos (SQS/SNS/EventBridge). |
| Microservices | Serviços pequenos com deploy independente; complexidade migra pra operação. |
| Monolito distribuído | Anti-padrão: microservices acoplados que deployam juntos. |
| Pets vs. cattle | Servidores substituíveis por automação, não máquinas-estimação. |
| HRI | High Risk Issue — risco alto apontado pelo Well-Architected Tool. |
| Milestone | Foto da revisão num momento; permite medir a evolução. |
| RTO / RPO | Quanto tempo pra voltar / quanto dado se pode perder (aprofunda no M18). |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Cite os **6 pilares** e um exemplo de prática de cada — e explique por que eles **conflitam**.
2. No desenho de referência, por que o ALB fica em subnet **pública** e o RDS em **privada**?
3. Quando um **monolito** é a escolha certa? E o que é um "monolito distribuído"?
4. Qual a diferença de propósito entre **SQS** e **SNS/EventBridge** num desenho event-driven?
5. Sua empresa tem backup diário do banco, nunca testado. Qual anti-padrão é esse e qual o risco real?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
