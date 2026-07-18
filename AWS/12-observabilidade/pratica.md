# Módulo 12 — Observabilidade (Prática Guiada)

> Objetivo desta prática: montar um mini-stack de observabilidade de ponta a ponta — explorar
> métricas existentes, **publicar métrica custom**, criar **alarme com notificação por e-mail**
> (e dispará-lo de propósito), criar **log group** com retenção, mandar logs e consultá-los no
> **Logs Insights**, **auditar a si mesmo** no CloudTrail e fechar com um **mini-dashboard**.
>
> **Abordagem:** Console primeiro (pra ver), CLI depois (pra fixar).
>
> ⏱️ Tempo estimado: 60–75 min. 💵 Custo: **~US$ 0** — tudo dentro do Free Tier
> (10 alarmes, 5 GB de logs, 10 métricas custom, 3 dashboards). Teardown obrigatório no final.

---

## ⚠️ Antes de começar — leia isto

- Ficaremos dentro do Free Tier: **1** alarme, **1** métrica custom, **1** log group pequeno,
  **1** dashboard, **1** tópico SNS. Nada disso deve gerar cobrança — e removeremos tudo no teardown.
- A retenção do log group será definida na criação (**nunca** deixar "Never expire").
- Região: **us-east-1**, como sempre.

---

## Parte A — Explorar métricas existentes (Console)

### Passo 1 — Passear pelas métricas automáticas
1. Console → **CloudWatch** → menu **Metrics → All metrics**.
2. Veja os **namespaces** disponíveis (dependem do que você já criou no curso: `AWS/EC2`,
   `AWS/Lambda`, `AWS/S3`, `AWS/RDS`...). Entre em um deles.
3. Note as **dimensões**: em `AWS/EC2`, as métricas vêm "Per-Instance" (`InstanceId`); em
   `AWS/Lambda`, por `FunctionName`.
4. Selecione uma métrica (ex.: `Invocations` de uma Lambda antiga, ou `NumberOfObjects` de um
   bucket) e grafe. Na aba **Graphed metrics**, troque a estatística (Average → Sum → Maximum)
   e o período — veja o gráfico mudar.

> 🎯 Fixando a teoria: **namespace** organiza, **dimensão** identifica a série, **estatística +
> período** definem como os pontos são agregados. Sem entender isso, todo gráfico é chute.

---

## Parte B — Métrica custom via CLI

### Passo 2 — Publicar a métrica
Vamos fingir que uma aplicação chamada `LabObservabilidade` publica pedidos processados:

```bash
aws cloudwatch put-metric-data \
  --namespace "LabObservabilidade" \
  --metric-name PedidosProcessados \
  --dimensions Ambiente=lab \
  --value 5

# publique mais alguns pontos com valores diferentes (espere ~30s entre eles):
aws cloudwatch put-metric-data --namespace "LabObservabilidade" \
  --metric-name PedidosProcessados --dimensions Ambiente=lab --value 12
aws cloudwatch put-metric-data --namespace "LabObservabilidade" \
  --metric-name PedidosProcessados --dimensions Ambiente=lab --value 8
```

### Passo 3 — Ver a métrica aparecer
1. Console → CloudWatch → Metrics → procure o namespace **LabObservabilidade** (pode levar
   1–2 min pra aparecer).
2. Grafe `PedidosProcessados` com estatística **Sum** e período **1 minute**.

Ou pela CLI:
```bash
aws cloudwatch list-metrics --namespace LabObservabilidade --output table
```

> 💡 Sua aplicação real faria exatamente isso via SDK (ex.: `boto3`), a cada evento de negócio.
> Métrica custom é assim que "pedidos por minuto" vira gráfico, alarme e dashboard.

---

## Parte C — Alarme com notificação por e-mail (SNS)

### Passo 4 — Criar o tópico SNS e a assinatura
```bash
aws sns create-topic --name lab-observabilidade-alertas
# guarde o TopicArn retornado (algo como arn:aws:sns:us-east-1:123456789012:lab-observabilidade-alertas)

aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:SEU_ACCOUNT_ID:lab-observabilidade-alertas \
  --protocol email \
  --notification-endpoint seu-email@exemplo.com
```
**Abra seu e-mail e clique em "Confirm subscription"** — sem confirmar, nada chega.

### Passo 5 — Criar o alarme (Console, pra ver as peças)
1. CloudWatch → **Alarms → All alarms → Create alarm**.
2. **Select metric** → namespace `LabObservabilidade` → `PedidosProcessados` (Ambiente=lab).
3. Statistic: **Sum**, Period: **1 minute**.
4. Condição: **Greater than 50**. Em *Additional configuration*, veja o **Datapoints to alarm**
   (deixe 1 de 1) e o *Missing data treatment* (deixe `missing`).
5. Ação: estado **In alarm** → tópico `lab-observabilidade-alertas` → Next.
6. Nome: `lab-pedidos-alto` → Create alarm.
7. Observe o estado inicial: **INSUFFICIENT_DATA** (ainda não há datapoints suficientes no período).

### Passo 6 — Disparar o alarme de propósito (CLI)
Em vez de esperar a métrica subir, force o estado — é o jeito padrão de **testar o pipeline
de notificação**:

```bash
aws cloudwatch set-alarm-state \
  --alarm-name lab-pedidos-alto \
  --state-value ALARM \
  --state-reason "Teste de notificacao do modulo 12"
```

✅ Em ~1 min você deve receber o **e-mail de alarme**. Veja também o histórico:
```bash
aws cloudwatch describe-alarm-history --alarm-name lab-pedidos-alto \
  --query "AlarmHistoryItems[].{Quando:Timestamp,OQue:HistorySummary}" --output table
```

> 💡 O `set-alarm-state` é temporário: na próxima avaliação real da métrica, o alarme volta ao
> estado verdadeiro. Perfeito pra testar sem gerar carga de verdade.

---

## Parte D — Logs: log group, envio via CLI e Logs Insights

### Passo 7 — Criar o log group COM retenção
```bash
aws logs create-log-group --log-group-name /lab/observabilidade
aws logs put-retention-policy --log-group-name /lab/observabilidade --retention-in-days 7
```
> ⚠️ O segundo comando é o hábito que este módulo quer te dar: **todo log group nasce com
> retenção**. Sem ele, ficaria "Never expire" — custo eterno e crescente.

### Passo 8 — Enviar eventos de log
```bash
aws logs create-log-stream --log-group-name /lab/observabilidade --log-stream-name app-1

AGORA=$(date +%s000)
aws logs put-log-events \
  --log-group-name /lab/observabilidade \
  --log-stream-name app-1 \
  --log-events \
    timestamp=$AGORA,message="INFO pedido 101 processado em 120ms" \
    timestamp=$((AGORA+1000)),message="INFO pedido 102 processado em 95ms" \
    timestamp=$((AGORA+2000)),message="ERRO pedido 103 falhou: timeout no pagamento" \
    timestamp=$((AGORA+3000)),message="INFO pedido 104 processado em 110ms" \
    timestamp=$((AGORA+4000)),message="ERRO pedido 105 falhou: timeout no pagamento"
```

Confira que chegaram:
```bash
aws logs tail /lab/observabilidade
```

### Passo 9 — Consultar no Logs Insights (Console)
1. CloudWatch → **Logs → Logs Insights** → selecione o log group `/lab/observabilidade`
   (intervalo: última 1 hora).
2. Rode a consulta — só os erros, mais recentes primeiro:
   ```
   fields @timestamp, @message
   | filter @message like /ERRO/
   | sort @timestamp desc
   | limit 20
   ```
3. Agora uma agregação — contagem de erros:
   ```
   filter @message like /ERRO/
   | stats count() as total_erros
   ```

> 🎯 `filter` + `stats` são o feijão-com-arroz do Insights. Em produção, é assim que você responde
> "quantos erros por minuto nas últimas 3 horas?" sem abrir log por log. Lembre: paga por GB
> **escaneado** — intervalo de tempo curto = consulta barata.

---

## Parte E — CloudTrail: quem fez o quê

### Passo 10 — Auditar a si mesmo
1. Console → **CloudTrail → Event history**. Sem configurar nada: os últimos **90 dias** de
   management events estão aí, **de graça**.
2. Filtre por **Event name** = `CreateLogGroup`. Ache o evento de minutos atrás: clique e veja o
   JSON — **quem** (seu usuário/ARN), **quando**, **de onde** (seu IP) e **o quê** (o log group criado).
3. Explore outros eventos recentes: `CreateTopic` (SNS), `PutMetricAlarm`...

Pela CLI:
```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=CreateLogGroup \
  --max-results 5 \
  --query "Events[].{Quando:EventTime,Quem:Username,Evento:EventName}" --output table
```

> 💡 É literalmente a resposta de "quem apagou o recurso?": filtre pelo event name
> (`DeleteBucket`, `TerminateInstances`...) e o autor aparece. Guarde essa carta na manga.

---

## Parte F — Mini-dashboard

### Passo 11 — Montar o painel
1. CloudWatch → **Dashboards → Create dashboard** → nome: `lab-observabilidade`.
2. Widget 1 — **Line**: métrica `LabObservabilidade / PedidosProcessados` (Sum, 1 min).
3. Widget 2 — **Alarm status**: selecione o alarme `lab-pedidos-alto`.
4. (Opcional) Widget 3 — **Logs table**: a query de erros do Passo 9.
5. Salve o dashboard.

> 🎯 Você acabou de montar a "TV da sala" de um serviço: tráfego (métrica), saúde (alarme) e
> diagnóstico (logs) num painel só. Free Tier: até 3 dashboards — o nosso é o primeiro.

---

## Parte G — 🔥 Teardown (obrigatório)

Tudo é Free Tier, mas o ritual é sagrado — e alarmes/dashboards extras um dia custam:

```bash
# 1. Alarme
aws cloudwatch delete-alarms --alarm-names lab-pedidos-alto

# 2. Dashboard
aws cloudwatch delete-dashboards --dashboard-names lab-observabilidade

# 3. Log group (leva os streams e eventos junto)
aws logs delete-log-group --log-group-name /lab/observabilidade

# 4. Tópico SNS (leva as assinaturas junto)
aws sns delete-topic \
  --topic-arn arn:aws:sns:us-east-1:SEU_ACCOUNT_ID:lab-observabilidade-alertas

# 5. Conferir que nada sobrou
aws cloudwatch describe-alarms --query "MetricAlarms[].AlarmName" --output table
aws logs describe-log-groups --log-group-name-prefix /lab --output table
aws sns list-topics --output table
```

> 💡 A métrica custom não precisa (nem pode) ser "apagada": métricas sem novos datapoints somem
> sozinhas da listagem após ~2 semanas e não custam nada paradas.

---

## ✅ Checklist de conclusão do módulo

- [ ] Explorou namespaces, dimensões e estatísticas nas métricas existentes.
- [ ] Publicou métrica custom com `put-metric-data` e a viu no gráfico.
- [ ] Criou tópico SNS e **confirmou a assinatura** por e-mail.
- [ ] Criou o alarme e entendeu os estados (nasceu `INSUFFICIENT_DATA`).
- [ ] Disparou o alarme com `set-alarm-state` e **recebeu o e-mail**.
- [ ] Criou log group **com retenção de 7 dias** (nunca "never expire").
- [ ] Enviou eventos de log via CLI e viu com `logs tail`.
- [ ] Rodou `filter` e `stats` no **Logs Insights**.
- [ ] Achou seus próprios eventos no **CloudTrail Event history** (Console e CLI).
- [ ] Montou o mini-dashboard com métrica + alarme.
- [ ] **Teardown completo**: alarme, dashboard, log group e tópico apagados.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-12/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-12/`) e para o **Módulo 13 — Segurança avançada**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 12" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
