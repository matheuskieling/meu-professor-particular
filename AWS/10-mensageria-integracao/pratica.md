# Módulo 10 — Mensageria & Integração (Prática Guiada)

> Objetivo desta prática: **viver** o ciclo de vida de uma mensagem SQS pela CLI (enviar,
> receber, ver o **visibility timeout** agindo, deletar), montar uma **DLQ** e forçar mensagens a
> caírem nela, construir o **fan-out SNS → e-mail + SQS**, e fechar com uma **regra agendada do
> EventBridge** disparando uma Lambda por minuto.
>
> **Abordagem:** este módulo é a alma da CLI — filas e mensagens são muito mais visíveis no
> terminal. O Console entra pra criar o tópico SNS e conferir o resultado.
>
> ⏱️ Tempo estimado: 60–75 min. 💵 Custo: **US$ 0** — SQS tem **1M requests/mês sempre grátis**,
> SNS 1M publicações, EventBridge não cobra por regras de agendamento, e a Lambda fica no
> sempre-grátis do Módulo 08.

---

## ⚠️ Antes de começar — leia isto

- Pré-requisitos: **Módulo 01** (CLI) e **Módulo 08** (Lambda — vamos recriar a `m08-hello` mínima
  se você já a destruiu no teardown, como manda o ritual).
- Região: **us-east-1** em tudo.
- Você vai precisar de um **e-mail** que consiga abrir (pra confirmar a subscription do SNS).

---

## Parte A — SQS: o ciclo de vida de uma mensagem (CLI)

### Passo 1 — Criar a fila
```bash
aws sqs create-queue --queue-name m10-fila
```
Guarde a URL retornada numa variável (vamos usar direto):
```bash
FILA=$(aws sqs get-queue-url --queue-name m10-fila --query QueueUrl --output text)
echo $FILA
```
Dê uma olhada no Console (**SQS**) também: fila Standard, visibility timeout 30 s, retenção 4 dias.

### Passo 2 — Enviar mensagens
```bash
aws sqs send-message --queue-url $FILA --message-body '{"pedido": 1, "valor": 99.90}'
aws sqs send-message --queue-url $FILA --message-body '{"pedido": 2, "valor": 45.00}'
```
> O `MD5OfMessageBody` retornado é só o recibo. As mensagens agora estão **duráveis** na fila,
> esperando um consumidor — o produtor já pode ir embora.

### Passo 3 — Receber… e entender o visibility timeout
```bash
aws sqs receive-message --queue-url $FILA --max-number-of-messages 2
```
Você recebeu a(s) mensagem(ns) **e um `ReceiptHandle`** (o "ticket" pra deletar depois). Agora o
experimento-chave — **receba de novo, imediatamente**:
```bash
aws sqs receive-message --queue-url $FILA
```
**Veio vazio!** As mensagens não sumiram: estão **invisíveis** pelo visibility timeout (30 s).
Espere ~30 s e rode de novo:
```bash
sleep 35 && aws sqs receive-message --queue-url $FILA
```
**Reapareceram** — porque você não deletou. Isso é o SQS assumindo que seu "consumidor" falhou e
oferecendo a mensagem de novo. **Receber ≠ consumir.**

### Passo 4 — Deletar (consumir de verdade)
Pegue o `ReceiptHandle` do último receive (precisa ser o **mais recente**) e delete:
```bash
aws sqs delete-message --queue-url $FILA --receipt-handle "COLE_O_RECEIPT_HANDLE_AQUI"
```
Repita receive+delete até a fila esvaziar. Confirme:
```bash
aws sqs get-queue-attributes --queue-url $FILA \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible
```

### Passo 5 — Long polling
```bash
aws sqs receive-message --queue-url $FILA --wait-time-seconds 20
```
A chamada **fica esperando** até 20 s (mande uma mensagem por outro terminal e veja ela chegar
na hora!). Em produção, isso vira o padrão da fila:
```bash
aws sqs set-queue-attributes --queue-url $FILA --attributes ReceiveMessageWaitTimeSeconds=20
```

---

## Parte B — DLQ: aparando as mensagens venenosas

### Passo 6 — Criar a DLQ e ligar a redrive policy
```bash
aws sqs create-queue --queue-name m10-dlq
DLQ=$(aws sqs get-queue-url --queue-name m10-dlq --query QueueUrl --output text)
DLQ_ARN=$(aws sqs get-queue-attributes --queue-url $DLQ --attribute-names QueueArn --query Attributes.QueueArn --output text)

aws sqs set-queue-attributes --queue-url $FILA --attributes "{
  \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"2\\\"}\"
}"
```
> Traduzindo a redrive policy: "se uma mensagem for recebida **2 vezes** sem ser deletada, mova
> pra `m10-dlq`". Em produção usa-se 3–5; usamos 2 pra ver rápido.

### Passo 7 — Forçar uma mensagem a cair na DLQ
Simule um consumidor bugado: recebe, "falha" (não deleta), e a mensagem volta… duas vezes:
```bash
aws sqs send-message --queue-url $FILA --message-body '{"pedido": 666, "valor": "PAYLOAD_QUEBRADO"}'

# 1º recebimento (não deleta = simula crash)
aws sqs receive-message --queue-url $FILA --visibility-timeout 5
sleep 6

# 2º recebimento (estourou o maxReceiveCount=2)
aws sqs receive-message --queue-url $FILA --visibility-timeout 5
sleep 6

# 3ª tentativa: a fila principal está vazia...
aws sqs receive-message --queue-url $FILA
# ...e a mensagem está na DLQ!
aws sqs receive-message --queue-url $DLQ
```
> 🎯 O `--visibility-timeout 5` por chamada só acelera o experimento. O que você viu é o
> mecanismo real que evita loop infinito de mensagem venenosa — e ela ficou **preservada** na DLQ
> pra análise. No Console, a aba da DLQ ainda oferece **redrive** (devolver pra principal após o fix).

---

## Parte C — SNS: fan-out pra e-mail + fila

### Passo 8 — Criar o tópico e a subscription de e-mail (Console)
1. Console → **SNS** → **Topics** → **Create topic** → tipo **Standard**, nome `m10-avisos`.
2. **Create subscription** → Protocol: **Email** → seu e-mail → **Create**.
3. **Abra seu e-mail e clique em "Confirm subscription"** (sem isso, nada chega!).

### Passo 9 — Inscrever a fila SQS no tópico (fan-out)
A CLI aqui ensina o detalhe que o Console esconde — a **queue policy** autorizando o SNS:
```bash
TOPICO=$(aws sns create-topic --name m10-avisos --query TopicArn --output text)  # retorna o ARN do existente
FILA_ARN=$(aws sqs get-queue-attributes --queue-url $FILA --attribute-names QueueArn --query Attributes.QueueArn --output text)

# 1) Permitir que o tópico envie pra fila
aws sqs set-queue-attributes --queue-url $FILA --attributes "{
  \"Policy\": \"{\\\"Version\\\":\\\"2012-10-17\\\",\\\"Statement\\\":[{\\\"Effect\\\":\\\"Allow\\\",\\\"Principal\\\":{\\\"Service\\\":\\\"sns.amazonaws.com\\\"},\\\"Action\\\":\\\"sqs:SendMessage\\\",\\\"Resource\\\":\\\"$FILA_ARN\\\",\\\"Condition\\\":{\\\"ArnEquals\\\":{\\\"aws:SourceArn\\\":\\\"$TOPICO\\\"}}}]}\"
}"

# 2) Criar a subscription SQS
aws sns subscribe --topic-arn $TOPICO --protocol sqs --notification-endpoint $FILA_ARN
```

### Passo 10 — Publicar e ver o fan-out
```bash
aws sns publish --topic-arn $TOPICO \
  --subject "Pedido criado" \
  --message '{"pedido": 42, "valor": 199.90}'
```
Agora confira os **dois destinos da mesma publicação**:
1. 📧 Chegou um e-mail no seu inbox.
2. 📥 A fila recebeu uma cópia:
```bash
aws sqs receive-message --queue-url $FILA
```
> Repare que a mensagem na fila vem **embrulhada** num JSON do SNS (`Type`, `TopicArn`,
> `Message`...). É o envelope da teoria — `RawMessageDelivery` na subscription tira o embrulho.
> **Isso é fan-out:** 1 publish, N entregas, e o publicador não conhece nenhum destino.

---

## Parte D — EventBridge: agendamento disparando Lambda

### Passo 11 — Garantir a Lambda alvo
Se você destruiu a `m08-hello` no teardown do Módulo 08 (👏), recrie a versão mínima: Console →
Lambda → **Create function** → `m10-ping`, Python 3.13, role básica, código:
```python
def lambda_handler(event, context):
    print(f"Ping do EventBridge! event={event}")
    return "pong"
```
**Deploy.** (Se a `m08-hello` ainda existe, use-a e ajuste o nome nos comandos.)

### Passo 12 — Criar a regra agendada + permissão + target
```bash
# 1) Regra: dispara a cada 1 minuto
aws events put-rule --name m10-cada-minuto --schedule-expression "rate(1 minute)"

# 2) Permitir que o EventBridge invoque a função (resource-based policy, como no trigger S3!)
CONTA=$(aws sts get-caller-identity --query Account --output text)
aws lambda add-permission \
  --function-name m10-ping \
  --statement-id m10-eventbridge \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:$CONTA:rule/m10-cada-minuto

# 3) Apontar a regra pra Lambda
FN_ARN=$(aws lambda get-function --function-name m10-ping --query Configuration.FunctionArn --output text)
aws events put-targets --rule m10-cada-minuto --targets "Id"="1","Arn"="$FN_ARN"
```

### Passo 13 — Ver o cron da nuvem batendo
Espere 1–2 minutos e acompanhe:
```bash
aws logs tail /aws/lambda/m10-ping --since 5m --follow
```
Um "Ping do EventBridge!" por minuto. Você montou um **agendador serverless** sem nenhum servidor
de cron. (`Ctrl+C` pra sair do follow.) Repare no `event` logado: é o evento padrão
`aws.events`/`Scheduled Event` — um event pattern poderia filtrá-lo num barramento.

> ⚠️ Não deixe a regra ativa por dias sem necessidade: são 1.440 invocações/dia. Free Tier
> aguenta fácil, mas é ruído — e o teardown já vem a seguir.

---

## Parte E — 🔥 Teardown (obrigatório)

Ordem: regra do EventBridge → Lambda → SNS → filas.

```bash
# 1. EventBridge: targets primeiro, depois a regra
aws events remove-targets --rule m10-cada-minuto --ids 1
aws events delete-rule --name m10-cada-minuto

# 2. Lambda + log group
aws lambda delete-function --function-name m10-ping
aws logs delete-log-group --log-group-name /aws/lambda/m10-ping

# 3. SNS: subscriptions e tópico
aws sns list-subscriptions-by-topic --topic-arn $TOPICO \
  --query "Subscriptions[].SubscriptionArn" --output text
# para cada ARN listado (o de e-mail pode aparecer como PendingConfirmation — some com o tópico):
aws sns unsubscribe --subscription-arn ARN_DA_SUBSCRIPTION_SQS
aws sns delete-topic --topic-arn $TOPICO

# 4. Filas (SQS impede recriar com o mesmo nome por ~60s, tudo bem)
aws sqs delete-queue --queue-url $FILA
aws sqs delete-queue --queue-url $DLQ
```

Confira no Console: SQS, SNS, EventBridge (Rules) e Lambda **vazios**.

---

## ✅ Checklist de conclusão do módulo

- [ ] Criou `m10-fila` e enviou mensagens pela CLI.
- [ ] **Viu o visibility timeout agindo**: receive → invisível → reapareceu sem delete.
- [ ] Deletou mensagens com o `ReceiptHandle` e usou **long polling** (`--wait-time-seconds`).
- [ ] Configurou a **redrive policy** (`maxReceiveCount=2`) e viu a mensagem cair na **DLQ**.
- [ ] Criou o tópico `m10-avisos` com subscription de **e-mail confirmada**.
- [ ] Fez o **fan-out**: 1 publish chegou no e-mail **e** na fila (com o envelope do SNS).
- [ ] Regra EventBridge `rate(1 minute)` invocou a Lambda e você viu no `logs tail`.
- [ ] **Teardown completo** (regra, Lambda, tópico, filas).

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-10/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-10/`) e para o **Módulo 11 — Infra como Código (IaC)**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 10" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
