# Módulo 10 — Mensageria & Integração (Teoria)

> Objetivo do módulo: entender **por que desacoplar** sistemas (a motivação por trás de tudo),
> dominar o **SQS** (filas), o **SNS** (pub/sub e fan-out) e o **EventBridge** (barramento de
> eventos), saber **qual usar quando**, e conhecer os **padrões** que aparecem em toda
> arquitetura séria: fan-out, fila de trabalho, retry/DLQ e idempotência. Este módulo fecha o
> tripé do event-driven que começamos no Módulo 08.

---

## 1. Por que desacoplar — síncrono vs. assíncrono

Imagine um e-commerce onde o serviço de Pedidos chama **diretamente** (HTTP síncrono) o de
Pagamentos, que chama o de Nota Fiscal, que chama o de E-mail. Três problemas clássicos:

1. **Falha em cascata** — o serviço de e-mail caiu → a nota trava → o pagamento trava → o
   cliente vê erro no checkout. Um componente periférico derrubou a venda.
2. **Picos** — na Black Friday chegam 10x mais pedidos. Todos os serviços da cadeia precisam
   aguentar o pico **ao mesmo tempo**, ou tudo degrada junto.
3. **Acoplamento** — Pedidos precisa conhecer endereço, contrato e disponibilidade de todo mundo.
   Adicionar um consumidor novo ("analytics quer saber de cada pedido") = mexer no produtor.

A solução: colocar um **intermediário durável** no meio — uma fila ou um barramento:

```
síncrono:   Pedidos ──HTTP──▶ Processador        (os dois precisam estar de pé, na mesma hora)
assíncrono: Pedidos ──▶ [ fila ] ──▶ Processador (cada um no seu ritmo)
```

O que muda com o assíncrono:

- **Absorção de picos** — a fila é o "amortecedor": chegam 10.000 pedidos num minuto? Ficam
  guardados; o consumidor processa no ritmo dele (e escala com calma).
- **Tolerância a falhas** — consumidor caiu? As mensagens **esperam** na fila. Voltou, processa.
  Ninguém perdeu venda.
- **Desacoplamento** — produtor e consumidor não se conhecem; evoluem e escalam separados.
- O **preço**: consistência eventual (o efeito acontece "logo", não "já") e a necessidade de
  pensar em duplicatas e ordenação — falamos disso na seção de padrões.

> 💡 Regra de bolso: se quem chama **precisa da resposta agora** (ex.: "o cartão foi aprovado?"),
> síncrono. Se é um **trabalho que pode acontecer em seguida** (e-mail, nota, thumbnail,
> relatório), assíncrono — e seu sistema fica mais barato e mais resiliente.

---

## 2. SQS — Simple Queue Service

O **SQS** é a fila gerenciada da AWS (um dos serviços mais antigos e mais sólidos). Produtores
**enviam** mensagens; consumidores **fazem poll**, processam e **deletam**. Totalmente
serverless: sem servidor, escala praticamente infinita, pague por requisição.

### O ciclo de vida de uma mensagem (o coração do SQS)

1. Produtor faz `SendMessage` → mensagem armazenada (retenção padrão: 4 dias; máx: 14).
2. Consumidor faz `ReceiveMessage` → a mensagem **não é removida**: fica **invisível** pelo
   **visibility timeout** (padrão: 30 s).
3. Consumidor processa e chama `DeleteMessage` → só aí ela morre.
4. Se o consumidor **não deletar** dentro do visibility timeout (crashou? travou?), a mensagem
   **reaparece** na fila pra outro consumidor tentar.

> 🎯 Esse desenho é a genialidade do SQS: **receber ≠ consumir**. O delete explícito garante que
> uma mensagem só some depois de processada com sucesso — falha no meio = retry automático.

> ⚠️ **Armadilha clássica:** visibility timeout **menor** que o tempo de processamento → a
> mensagem reaparece **enquanto ainda está sendo processada** → dois consumidores processam a
> mesma mensagem. Regra: timeout ≥ tempo máximo de processamento (com folga; e é ajustável por
> mensagem via `ChangeMessageVisibility`).

### Standard vs. FIFO

| | **Standard** (padrão) | **FIFO** (nome termina em `.fifo`) |
|---|---|---|
| Entrega | **At-least-once** (pode duplicar!) | **Exactly-once** (deduplicação de 5 min) |
| Ordem | Best-effort (pode embaralhar) | **Estrita** por message group |
| Throughput | Praticamente ilimitado | 300 msg/s (3.000 com batching; mais no high throughput mode) |
| Quando | Quase sempre: trabalho paralelo onde ordem não importa | Ordem/unicidade obrigatórias (financeiro, eventos sequenciais) |

FIFO usa **message group ID** (ordem garantida *dentro* do grupo; grupos em paralelo) e
**deduplication ID** (mensagens repetidas em 5 min são descartadas).

### Long polling

`ReceiveMessage` padrão (**short polling**) responde na hora, mesmo vazio — um loop de consumo
vira metralhadora de requisições vazias (e requisição custa). Com **long polling**
(`WaitTimeSeconds` até **20 s**), a chamada **espera** mensagem chegar antes de responder:
menos requisições, menos custo, entrega mais rápida. **Use sempre** (dá pra definir como padrão
da fila via `ReceiveMessageWaitTimeSeconds`).

### DLQ — Dead-Letter Queue

E a mensagem **venenosa** — aquela que sempre falha (payload corrompido, bug)? Sem proteção, ela
fica em loop eterno: reaparece, falha, reaparece... A solução é a **DLQ**: uma fila comum
configurada como destino de descarte. Na fila principal você define uma **redrive policy**:
"após **`maxReceiveCount`** recebimentos (ex.: 3) sem delete, mova pra DLQ".

Benefícios: o loop para, a fila principal flui, e as mensagens problemáticas ficam **guardadas
pra análise** (e podem voltar depois do fix — *redrive*). Coloque um **alarme** na DLQ: mensagem
lá = algo quebrou.

---

## 3. SNS — Simple Notification Service

O SQS é **1 fila → consumidores puxam**. O **SNS** é o inverso: **pub/sub por push**. Você
publica uma mensagem num **tópico**, e o SNS **empurra uma cópia pra cada subscription**:

- **Subscriptions suportadas:** filas SQS, funções Lambda, endpoints HTTP/S, e-mail, SMS, push
  mobile, Kinesis Firehose.
- **Fan-out:** 1 publicação → N destinos, em paralelo. O publicador não sabe (nem quer saber)
  quantos são.
- **Sem retenção pra consumo posterior:** o SNS entrega e pronto — quem não estava inscrito no
  momento, perdeu (entrega tem retry por protocolo, mas não é uma fila pra "buscar depois").
- **Filter policies:** cada subscription pode filtrar por atributos da mensagem ("só me entregue
  eventos com `tipo = pedido_grande`") — filtro no barramento, não no consumidor.

### O padrão de ouro: SNS → SQS (fan-out durável)

Push direto num consumidor é frágil (caiu, perdeu). Por isso o padrão clássico casa os dois:

```
                      ┌──▶ fila SQS (cobrança)   ──▶ worker
publicador ──▶ tópico ├──▶ fila SQS (nota fiscal) ──▶ worker
                      └──▶ fila SQS (analytics)  ──▶ worker
```

Cada consumidor ganha **sua própria fila** — com buffer, retry e DLQ próprios. O melhor dos dois
mundos: a distribuição do SNS + a durabilidade do SQS.

> 💡 Detalhe prático dessa integração: (1) a fila precisa de uma **queue policy** permitindo ao
> tópico fazer `SendMessage`; (2) ative **raw message delivery** na subscription se não quiser a
> mensagem embrulhada no JSON de envelope do SNS.

---

## 4. EventBridge — o barramento de eventos

O **EventBridge** é o serviço de **event bus** da AWS: eventos (JSON) entram no barramento, e
**regras** (rules) decidem pra onde vão.

- **Barramentos:** o `default` (recebe eventos dos próprios serviços AWS — "instância EC2 mudou
  de estado", "objeto criado no S3"...), barramentos **custom** (seus eventos de negócio) e
  **partner** (SaaS de terceiros: Datadog, Stripe, Shopify...).
- **Regras com event patterns:** filtram pelo **conteúdo** do evento (JSON pattern matching).
  Ex.: `source = "meu.app"` **e** `detail.tipo = "pedido_criado"` → manda pros targets.
- **Targets:** 20+ tipos por regra — Lambda, SQS, SNS, Step Functions, ECS task, outra API...
- **Scheduler:** o EventBridge também agenda — expressões `rate(5 minutes)` ou cron
  (`cron(0 12 * * ? *)`) disparando targets. É o "crontab da nuvem" (o serviço novo dedicado é o
  **EventBridge Scheduler**, ainda mais flexível).

### SQS vs. SNS vs. EventBridge — o comparativo que cai em toda prova

| | **SQS** | **SNS** | **EventBridge** |
|---|---|---|---|
| Modelo | Fila (pull) | Pub/sub (push) | Barramento com regras (push) |
| Consumidores | 1 fila, N workers **dividem** as mensagens | Todos os subscribers recebem **cópia** | Targets das regras que **casarem** |
| Retenção/buffer | ✅ até 14 dias | ❌ entrega imediata | ❌ (mas retry + DLQ por target) |
| Filtro | ❌ (consome tudo) | Por atributos | Por **conteúdo** do evento (rico) |
| Forte em | Fila de trabalho, absorver picos | Fan-out simples, notificações | Roteamento por conteúdo, eventos AWS/SaaS, agendamento |

Regra de bolso:
- **Preciso de buffer/trabalho distribuído entre workers** → **SQS**.
- **Um evento, vários interessados, simples e barato** → **SNS** (idealmente → SQS).
- **Roteamento por conteúdo, integrar eventos da AWS/SaaS, agendar, arquitetura de eventos
  "de verdade"** → **EventBridge**.
- E eles se **combinam**: EventBridge → SQS, SNS → SQS, EventBridge → Lambda → SQS...

---

## 5. Padrões essenciais de mensageria

### Fila de trabalho (work queue)
N produtores → 1 fila → N workers **competindo** pelas mensagens. Cada mensagem é processada por
**um** worker. Escala horizontal trivial: fila crescendo? Adicione workers (com Lambda + SQS,
isso é automático). É o padrão pra e-mails, thumbnails, relatórios, qualquer "trabalho em lote".

### Fan-out
1 evento → N consumidores **independentes**, cada um com sua cópia. Implementação canônica:
**SNS → várias SQS** (ou EventBridge com várias regras/targets). Adicionar consumidor novo =
criar fila + subscription; **o produtor não muda**.

### Retry com DLQ
Falhou? Tenta de novo (o visibility timeout dá isso de graça no SQS). Continuou falhando
`maxReceiveCount` vezes? **DLQ** + alarme + análise humana. Sem DLQ, mensagem venenosa vira loop
infinito; sem retry, qualquer soluço vira perda.

### Idempotência — o padrão que amarra tudo
SQS standard é **at-least-once**: a duplicata **vai** acontecer (e reprocessamento pós-falha
também). A defesa é o consumidor ser **idempotente**: processar a mesma mensagem 2x tem o
**mesmo efeito** que 1x.

Técnicas: chave única de negócio (`pedido_id`) + verificação antes de agir ("já processei esse
id? ignora"), operações naturalmente idempotentes (`SET status = 'pago'` em vez de
`ADD saldo + 10`), constraint única no banco segurando a segunda escrita.

> ⚠️ **Armadilha clássica de prova e de vida:** "uso FIFO e estou livre de duplicatas". A
> deduplicação do FIFO cobre uma janela de **5 minutos na publicação** — não protege contra o
> **seu consumidor** falhar após processar e antes de deletar (a mensagem volta!). **Idempotência
> no consumidor é obrigatória sempre.**

---

## 6. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Desacoplamento | Produtor e consumidor não se conhecem; falham e escalam separados. |
| SQS | Fila gerenciada (pull): buffer durável entre produtores e consumidores. |
| Visibility timeout | Janela em que a mensagem recebida fica invisível; sem delete, ela reaparece. |
| Standard vs. FIFO | At-least-once/ordem best-effort vs. exactly-once/ordem estrita (menor throughput). |
| Long polling | ReceiveMessage que espera (até 20 s) mensagem chegar — menos custo, use sempre. |
| DLQ | Fila de descarte pra mensagens que falharam `maxReceiveCount` vezes (redrive policy). |
| SNS | Pub/sub por push: publica num tópico, todas as subscriptions recebem cópia. |
| Fan-out | 1 evento → N consumidores; padrão canônico: SNS → várias filas SQS. |
| EventBridge | Barramento de eventos com regras que filtram por conteúdo + agendamento (cron/rate). |
| Event pattern | O filtro JSON de uma regra do EventBridge. |
| Idempotência | Processar a mesma mensagem 2x tem o mesmo efeito que 1x — obrigatória no consumidor. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Cite os **três problemas** do acoplamento síncrono que uma fila resolve — e o preço que se
   paga pelo assíncrono.
2. Explique o **visibility timeout**: o que acontece se o consumidor crashar no meio do
   processamento? E se o timeout for curto demais?
3. Quando você escolheria **FIFO** em vez de Standard — e o que você perde na troca?
4. Desenhe (mentalmente) o **fan-out SNS → SQS** de um evento "pedido criado" com 3 interessados.
   Por que não entregar do SNS direto nos consumidores?
5. Por que **idempotência** no consumidor é obrigatória mesmo usando fila FIFO?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
