# Módulo 12 — Observabilidade (Teoria)

> Objetivo do módulo: sair do "acho que está tudo bem" para o **saber** — medir, registrar,
> alertar e auditar tudo que roda na sua conta. Você vai dominar o **CloudWatch** (métricas,
> logs, alarmes, dashboards), entender o **CloudTrail** (quem fez o quê), conhecer o **X-Ray**
> (rastreamento distribuído) e ver como o **EventBridge** reage a eventos de infraestrutura.
> Sem observabilidade, você opera no escuro; com ela, incidentes viram diagnósticos.

---

## 1. Os três pilares: métricas, logs e traces

**Observabilidade** é a capacidade de entender o estado interno de um sistema olhando o que ele
emite pra fora. O modelo clássico tem três pilares — cada um responde uma pergunta diferente:

| Pilar | O que é | Pergunta que responde | Serviço AWS |
|-------|---------|-----------------------|-------------|
| **Métricas** | Números ao longo do tempo (CPU %, requisições/s, latência) | "**Quanto?** Está dentro do normal?" | CloudWatch Metrics |
| **Logs** | Registros de eventos em texto, com timestamp | "**O que aconteceu** exatamente, e em que ordem?" | CloudWatch Logs |
| **Traces** | O caminho de UMA requisição através de vários serviços | "**Onde** a requisição gastou tempo / falhou?" | AWS X-Ray |

> 💡 Analogia médica: métricas são os **sinais vitais** (febre? pressão?); logs são o **prontuário**
> (o relato detalhado do que houve); traces são o **exame de contraste** (por onde o problema passou).
> Diagnóstico bom usa os três: a métrica te *acorda*, o trace te *localiza*, o log te *explica*.

Complementos do modelo: **alarmes** (agir quando uma métrica sai do normal), **dashboards**
(ver tudo num painel) e **auditoria** (CloudTrail: quem fez cada chamada de API).

---

## 2. CloudWatch Metrics — os números da sua conta

O **CloudWatch** é o serviço central de monitoramento. Praticamente todo serviço AWS publica
métricas nele **automaticamente**: EC2 manda CPU e rede, S3 manda tamanho de bucket, Lambda manda
invocações e erros, RDS manda conexões...

Conceitos que estruturam tudo:

- **Namespace** — a "pasta" da métrica: `AWS/EC2`, `AWS/Lambda`, `AWS/RDS`... Métricas suas
  (custom) vão em namespaces seus (ex.: `MeuApp`).
- **Métrica** — o nome do número medido: `CPUUtilization`, `Invocations`, `Latency`.
- **Dimensões** — pares chave/valor que **identificam** de quem é a métrica: `InstanceId=i-0abc...`,
  `FunctionName=minha-funcao`. A mesma métrica com dimensões diferentes são séries **separadas**.
- **Estatísticas** — como agregar os pontos num período: `Average`, `Sum`, `Maximum`, `Minimum`,
  percentis (`p99` — essencial pra latência: a média esconde os piores casos).
- **Resolução** — padrão (*standard*): granularidade de **1 minuto**; alta resolução (*high
  resolution*): até **1 segundo** (custom metrics, custa mais).

### Métricas custom

Sua aplicação pode publicar qualquer número com `put-metric-data`: pedidos processados, fila
interna, tempo de resposta de um parceiro... Vira cidadão de primeira classe: dá pra grafar,
alarmar e colocar em dashboard como qualquer métrica da AWS.

> ⚠️ **Armadilhas de métricas:**
> 1. No EC2, a métrica de **memória RAM não existe por padrão** — o hypervisor não enxerga dentro
>    do SO. Precisa do **CloudWatch Agent** instalado na instância (mesma coisa pra disco usado).
> 2. Métricas custom **custam** por métrica/mês fora do Free Tier — dimensões demais (ex.: uma
>    dimensão por usuário) explodem em milhares de séries e a fatura vem junto ("cardinality bomb").

---

## 3. CloudWatch Logs — os registros

Estrutura em dois níveis:

- **Log group** — o agrupador lógico, normalmente um por aplicação/recurso (ex.:
  `/aws/lambda/minha-funcao`). É nele que você define **retenção** e permissões.
- **Log stream** — uma sequência de eventos de **uma fonte** dentro do grupo (uma instância,
  um container, uma execução).

Serviços gerenciados (Lambda, ECS, RDS...) mandam logs sozinhos; no EC2, de novo, é o
**CloudWatch Agent** quem envia os arquivos de log do SO/aplicação.

> ⚠️ **A armadilha de custo nº 1 deste módulo:** a retenção padrão de um log group é
> **"Never expire"** — os logs ficam pra sempre, e armazenamento de log **custa por GB/mês**,
> além do custo de ingestão. Anos de logs esquecidos viram uma fatura silenciosa e crescente.
> **Hábito profissional:** todo log group nasce com retenção definida (7, 30, 90 dias — o que o
> caso pedir). Nós faremos isso na prática.

### Logs Insights

Consultar logs "no olho" não escala. O **Logs Insights** dá uma linguagem de consulta sobre os
log groups — pense num "SQL de logs":

```
fields @timestamp, @message
| filter @message like /ERRO/
| sort @timestamp desc
| limit 20
```

Comandos centrais: `fields` (o que mostrar), `filter` (onde), `stats` (agregações —
`stats count() by bin(5m)` conta eventos por janela de 5 min), `sort`, `limit`, e `parse`
(extrair campos de texto livre). Você paga por **GB escaneado** — filtre por intervalo de tempo curto.

---

## 4. CloudWatch Alarms — de olhar para agir

Um **alarme** vigia uma métrica e muda de estado conforme um limiar. Os três estados:

| Estado | Significado |
|--------|-------------|
| `OK` | A métrica está dentro do limiar. |
| `ALARM` | A métrica violou o limiar pelo período configurado. |
| `INSUFFICIENT_DATA` | Não há dados suficientes pra decidir (recém-criado, ou a fonte parou de publicar). |

Anatomia: métrica + estatística (ex.: `Average`) + período (ex.: 5 min) + limiar (ex.: > 80) +
**datapoints to alarm** (ex.: 2 de 3 períodos — evita alarme por pico momentâneo).

**Ações** ao mudar de estado:
- **Notificar** via **SNS** → e-mail, SMS, webhook (PagerDuty/Slack). O padrão: alarme → tópico SNS → subscribers.
- **Auto Scaling** → adicionar/remover instâncias.
- **EC2 actions** → parar/reiniciar/recuperar a instância.

> 💡 `INSUFFICIENT_DATA` não é decorativo: se um alarme de "aplicação viva" cai nesse estado, pode
> significar que **a fonte morreu** e parou de publicar. Trate a ausência de dados como sinal
> (configure o *treat missing data* de acordo — ex.: `breaching` pra heartbeats).

### Composite alarms

Um **composite alarm** combina outros alarmes com lógica booleana (`ALARM(a) AND ALARM(b)`).
Uso clássico: reduzir ruído — só acordar alguém de madrugada se CPU **e** erros **e** latência
dispararem juntos, em vez de três pages separados.

### Dashboards

**Dashboards** juntam gráficos de métricas (e queries de logs) num painel — a "TV da sala" do time.
São **globais** (um dashboard mostra métricas de várias regiões). Free Tier: **3 dashboards**
(até 50 métricas cada). Bom dashboard responde em 10 segundos: *"está tudo bem?"* — poucos
gráficos essenciais (erros, latência, tráfego, saturação), não um mosaico de 40 widgets.

---

## 5. CloudTrail — quem fez o quê

Se CloudWatch responde "como o sistema **está**", o **CloudTrail** responde "**quem fez o quê,
quando e de onde**". Ele grava (quase) **toda chamada de API** na conta — do Console, da CLI, dos
SDKs e dos próprios serviços. Cada evento traz: identidade (quem), ação (o quê: `RunInstances`,
`DeleteBucket`...), origem (IP, user agent), timestamp e parâmetros.

Dois tipos de evento:

| Tipo | O que cobre | Exemplo | Custo |
|------|-------------|---------|-------|
| **Management events** | Operações de **gestão** (plano de controle): criar/alterar/apagar recursos | `RunInstances`, `CreateBucket`, `PutRolePolicy` | **Event history: grátis** |
| **Data events** | Operações **nos dados** (alto volume) | `GetObject`/`PutObject` no S3, `Invoke` no Lambda | Pagos, desligados por padrão |

- **Event history** — os últimos **90 dias** de management events, **de graça, já ligado** em toda
  conta, consultável no Console/CLI. É sua primeira parada em qualquer investigação.
- **Trail** — pra guardar **além de 90 dias** (auditoria/compliance), você cria um *trail* que
  entrega os eventos num bucket S3 (paga o armazenamento; a primeira cópia de management events é grátis).

> 💡 CloudTrail é a ferramenta do *"quem apagou a instância?!"*. Na prática você vai se auditar:
> ver seus próprios comandos dos módulos anteriores registrados, com IP e identidade.

---

## 6. X-Ray — rastreamento distribuído (visão geral)

Numa arquitetura de microsserviços, uma requisição pode passar por API Gateway → Lambda → DynamoDB
→ SQS → outro Lambda... Se ficou lenta, **onde**? Logs de cada serviço são ilhas isoladas.

O **X-Ray** costura essas ilhas: cada requisição ganha um **trace ID** que a acompanha de serviço
em serviço. Cada trecho vira um **segmento** com duração e status. Resultado:

- **Service map** — o grafo visual dos serviços, com latências e taxas de erro em cada nó.
- **Traces** — a linha do tempo de uma requisição específica: "gastou 2,3 s, sendo 1,9 s numa
  query do DynamoDB" → achou o gargalo.

Exige instrumentação (SDK do X-Ray na aplicação ou suporte nativo — Lambda e API Gateway têm por
configuração). Neste módulo é só visão geral: o conceito de tracing importa mais que o passo a passo.

---

## 7. EventBridge — reagindo a eventos de infraestrutura

O **EventBridge** (você o conheceu na mensageria, Módulo 10) tem um papel central em observabilidade:
os serviços AWS **emitem eventos** de tudo que acontece — instância mudou de estado, alarme disparou,
GuardDuty achou ameaça, CloudTrail registrou uma chamada — e o EventBridge permite **reagir** com regras:

```
Evento (padrão JSON)              →  Regra (filtro)           →  Alvo (ação)
"EC2 Instance State-change:          casa com o padrão            Lambda, SNS, SQS,
 stopped"                                                          Step Functions...
```

Exemplos práticos: instância parou → notifica o time; access key criada (via CloudTrail) → dispara
auditoria automática; alarme entrou em `ALARM` → aciona runbook de remediação. É o trilho da
**resposta automática a incidentes**: o passo além de "ser avisado" é "reagir sozinho".

---

## 8. Custos e Free Tier do módulo

| Item | Free Tier | Depois |
|------|-----------|--------|
| Alarmes | **10** alarmes (resolução padrão) | ~US$ 0,10/alarme/mês |
| Logs | **5 GB** de ingestão + armazenamento | Paga por GB ingerido e por GB/mês armazenado |
| Métricas custom | **10** métricas | ~US$ 0,30/métrica/mês |
| Dashboards | **3** (até 50 métricas) | ~US$ 3/dashboard/mês |
| CloudTrail event history | 90 dias grátis (management) | Trails/data events pagam |
| Logs Insights | Paga por GB **escaneado** | — |

> 🎯 Nossa prática cabe **inteira no Free Tier** (~US$ 0). Mesmo assim: teardown no final —
> alarme, dashboard, log group e tópico SNS serão apagados.

---

## 9. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Observabilidade | Entender o estado interno do sistema pelo que ele emite (métricas, logs, traces). |
| Namespace | A "pasta" de uma métrica (`AWS/EC2`, `MeuApp`). |
| Dimensão | Chave/valor que identifica a série da métrica (`InstanceId=...`). |
| Resolução | Granularidade da métrica: padrão (1 min) ou alta (até 1 s). |
| Log group / stream | Agrupador de logs (com retenção) / sequência de uma fonte dentro dele. |
| Retenção | Por quanto tempo os logs vivem; padrão perigoso: **never expire**. |
| Logs Insights | Linguagem de consulta sobre logs (fields, filter, stats...). |
| Alarme | Vigia uma métrica; estados OK / ALARM / INSUFFICIENT_DATA; age via SNS etc. |
| Composite alarm | Combinação booleana de alarmes pra reduzir ruído. |
| CloudTrail | Auditoria: registro de (quase) toda chamada de API — quem, o quê, quando, de onde. |
| Management vs. data events | Gestão de recursos (grátis no history) vs. operações nos dados (pagas). |
| X-Ray / trace / segmento | Rastreia uma requisição entre serviços; o caminho e o tempo em cada trecho. |
| EventBridge | Regras que reagem a eventos de infra disparando ações automáticas. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Diferencie os três pilares e diga qual pergunta cada um responde. Num incidente de lentidão,
   em que ordem você os usaria?
2. O que são **namespace** e **dimensões** de uma métrica? Por que dimensões com alta
   cardinalidade são um risco de custo?
3. Por que a retenção **"never expire"** dos log groups é uma armadilha, e qual é o hábito correto?
4. Explique os três estados de um alarme. Por que `INSUFFICIENT_DATA` pode ser um sinal grave?
5. Alguém apagou um bucket ontem. Onde você descobre **quem** foi, e por que isso não custa nada?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
