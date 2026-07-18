# Módulo 17 — Otimização de Custos (FinOps) (Prática Guiada)

> Objetivo desta prática: aplicar o ciclo FinOps **na sua própria conta**: fazer um tour pela
> fatura real do curso no **Cost Explorer**, ativar **cost allocation tags**, criar **budget por
> serviço**, ligar o **Cost Anomaly Detection**, **estimar** a arquitetura de referência no
> Pricing Calculator e fazer uma **caça a recursos zumbis** via CLI.
>
> **Abordagem:** Console primeiro (pra ver), CLI depois (pra fixar e automatizar).
>
> ⏱️ Tempo estimado: 60–90 min. 💵 Custo: **US$ 0** — tudo nesta prática é gratuito
> (Cost Explorer UI, tags, budgets com alerta, Anomaly Detection e comandos `describe-*` não cobram).

---

## ⚠️ Antes de começar — leia isto

- O **Cost Explorer** precisa estar habilitado; se for a primeira vez, os dados levam **até 24h**
  pra aparecer. Se você criou budget lá no Módulo 01, provavelmente já está ativo.
- Nada aqui cria recurso pago. A única "pegadinha" seria usar a **API** do Cost Explorer
  (`aws ce ...` cobra ~US$ 0,01 por chamada) — vamos usar **poucas** chamadas, avisando antes.
- Esta prática rende mais se você tiver histórico dos módulos anteriores na conta (mesmo centavos).

---

## Parte A — Tour guiado pelo Cost Explorer (Console)

### Passo 1 — Abrir e orientar-se
1. Console → busque **Billing and Cost Management** → menu lateral **Cost Explorer**.
2. Se pedir pra habilitar, habilite (grátis) — e volte amanhã se não houver dados ainda.
3. Ajuste o intervalo para **os últimos 3–6 meses**, granularidade **Monthly**.

### Passo 2 — Agrupar e investigar (a fatura real do curso)
1. Em **Group by**, escolha **Service**. Observe: quais serviços dominaram seu gasto até aqui?
   (Provavelmente NAT Gateway/EC2/RDS dos módulos de infra... reconhece os vilões da teoria?)
2. Troque a granularidade para **Daily** e olhe o último mês: consegue ver os "morrinhos" dos dias
   de prática e os vales dos dias sem uso? Isso é o pague-pelo-uso visível.
3. Agrupe por **Region** — o custo está todo em `us-east-1` como esperado, ou algo vazou pra outra
   região (lembra da armadilha do seletor)?
4. Explore **Filters**: filtre só **EC2** e agrupe por **Usage type** — repare em itens como
   `DataTransfer` e `NatGateway`; é assim que se acha o *porquê* de um custo.

> 🎯 Pergunta de FinOps pra responder agora: **"qual foi o serviço mais caro do curso até hoje, e
> em que dia ele custou mais?"** Se você respondeu com 3 cliques, a fase *Inform* está dominada.

---

## Parte B — Ativar cost allocation tags (Console)

### Passo 3 — Ativar as tags na fatura
1. **Billing and Cost Management** → **Cost allocation tags**.
2. Na aba **User-defined cost allocation tags**, localize tags que você já usou no curso
   (ex.: `Projeto`, `Ambiente`, `Name`). Selecione `Projeto` e `Ambiente` (se existirem) → **Activate**.
3. Na aba **AWS-generated**, ative `aws:createdBy` (opcional, mas útil pra auditoria).

> **Por quê:** só agora essas tags viram dimensões no Cost Explorer. Lembre: **não retroage** e
> leva até 24h. A partir de amanhã, você poderá agrupar por `Tag: Projeto` no Cost Explorer e ver
> o custo por projeto — teste amanhã e comprove.

---

## Parte C — Budget por serviço + Anomaly Detection (Console)

### Passo 4 — Criar um budget por serviço
1. **Billing** → **Budgets** → **Create budget** → **Customize (advanced)** → tipo **Cost budget**.
2. Nome: `budget-ec2-mensal`. Período **Monthly**, valor **US$ 5** (ajuste à sua realidade).
3. Em **Budget scope**, adicione filtro **Service = EC2-Instances** (ou *Elastic Compute Cloud*).
4. Alertas: um em **80% do valor real (Actual)** e outro em **100% do previsto (Forecasted)** —
   e-mail nos dois.
5. Crie. (Alertas de budget são **gratuitos**; não vamos configurar *budget actions* hoje — mas
   repare na tela em **Actions**, onde seria possível, por exemplo, parar instâncias ao estourar.)

### Passo 5 — Ativar o Cost Anomaly Detection
1. **Billing and Cost Management** → **Cost Anomaly Detection** → **Create monitor**.
2. Tipo: **AWS services** (monitora cada serviço individualmente) → nome `monitor-servicos`.
3. Crie uma **alert subscription**: nome `alerta-anomalias`, frequência **Daily summary**,
   seu e-mail, limiar (ex.: alertar anomalias acima de **US$ 1**).
4. Confirme. A partir de agora o ML aprende seu padrão e avisa desvios — **grátis**.

> 💡 Repare a complementaridade: o budget vigia **o teto que você definiu**; o monitor de anomalias
> vigia **o padrão que você nem sabia que tinha**.

---

## Parte D — Estimar a arquitetura de referência (Pricing Calculator)

### Passo 6 — Estimativa da arquitetura do Módulo 15
Abra <https://calculator.aws> → **Create estimate** e adicione (região `us-east-1`):

1. **Application Load Balancer**: 1 ALB, tráfego modesto (ex.: 1 LCU).
2. **EC2**: 2× `t3.small` Linux, 730h/mês, **On-Demand**. Anote o subtotal.
3. Ainda no EC2, mude o modelo pra **Compute Savings Plan 1 ano, no upfront** e compare o preço.
   Essa diferença percentual é o desconto da teoria, ao vivo.
4. **RDS for PostgreSQL**: 1× `db.t3.micro`, **Multi-AZ**, 20 GB gp3.
5. **S3**: 10 GB Standard + algumas dezenas de milhares de requests.
6. (Opcional) **CloudFront**: 50 GB de saída.

Salve/exporte a estimativa (link ou CSV). **Pergunta-chave:** qual componente domina o custo
mensal? A resposta costuma surpreender (spoiler: raramente é o S3 😄).

---

## Parte E — Caça aos recursos zumbis (CLI)

Agora a parte de gente grande: varrer a conta procurando dinheiro vazando. Todos os comandos
abaixo são `describe-*`/`list-*` — **somente leitura, custo zero**.

### Passo 7 — Volumes EBS soltos (estado `available`)
Volume `available` = não anexado a nenhuma instância = cobrando por GB-mês à toa.
```bash
aws ec2 describe-volumes \
  --filters Name=status,Values=available \
  --query "Volumes[].{ID:VolumeId,GB:Size,Tipo:VolumeType,Criado:CreateTime}" \
  --output table
```

### Passo 8 — Elastic IPs não associados
EIP solto cobra (~US$ 0,005/h) — e desde 2024 **todo** IPv4 público cobra, associado ou não.
```bash
aws ec2 describe-addresses \
  --query "Addresses[?AssociationId==null].{IP:PublicIp,AllocId:AllocationId}" \
  --output table
```

### Passo 9 — Snapshots órfãos
Snapshots seus cujo volume de origem não existe mais:
```bash
# 1) IDs de todos os volumes existentes
aws ec2 describe-volumes --query "Volumes[].VolumeId" --output text | tr '\t' '\n' | sort > /tmp/vols.txt

# 2) Seus snapshots + volume de origem
aws ec2 describe-snapshots --owner-ids self \
  --query "Snapshots[].{Snap:SnapshotId,Vol:VolumeId,GB:VolumeSize,Quando:StartTime}" \
  --output text | sort -k2 > /tmp/snaps.txt

# 3) Snapshots cujo volume NÃO está na lista de vivos = órfãos
join -1 2 -2 1 -v 1 /tmp/snaps.txt /tmp/vols.txt
```

### Passo 10 — Outros zumbis rápidos
```bash
# Instâncias PARADAS (não cobram compute, mas os volumes delas cobram)
aws ec2 describe-instances \
  --filters Name=instance-state-name,Values=stopped \
  --query "Reservations[].Instances[].{ID:InstanceId,Tipo:InstanceType,Nome:Tags[?Key=='Name']|[0].Value}" \
  --output table

# Log groups SEM retenção definida (crescem pra sempre)
aws logs describe-log-groups \
  --query "logGroups[?retentionInDays==null].logGroupName" --output table

# Volumes ainda em gp2 (candidatos a gp3, ~20% mais barato)
aws ec2 describe-volumes --filters Name=volume-type,Values=gp2 \
  --query "Volumes[].{ID:VolumeId,GB:Size}" --output table
```

### Passo 11 — Agir sobre o que encontrou
Para **cada achado**, decida: precisa existir? Se não:
```bash
aws ec2 delete-volume --volume-id vol-xxxxxxxx        # volume solto
aws ec2 release-address --allocation-id eipalloc-xxxx # EIP ocioso
aws ec2 delete-snapshot --snapshot-id snap-xxxxxxxx   # snapshot órfão
aws logs put-retention-policy --log-group-name NOME --retention-in-days 30
```
> ⚠️ **Delete é irreversível.** Confirme que o snapshot/volume não é o backup de algo importante
> antes de apagar. Na dúvida, tagueie `Revisar=true` e decida depois — zumbi identificado já não é
> mais invisível.

### Passo 12 — (Opcional, ~US$ 0,02) Ver a fatura pela CLI
A API do Cost Explorer cobra ~US$ 0,01/chamada. Se quiser, **duas** chamadas didáticas:
```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "-30 days" +%F),End=$(date +%F) \
  --granularity MONTHLY --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --query "ResultsByTime[].Groups[?Metrics.UnblendedCost.Amount>'0.001'].[Keys[0],Metrics.UnblendedCost.Amount]" \
  --output table
```
É o mesmo "group by Service" da Parte A — agora scriptável (base de relatórios automatizados).

---

## Parte F — Teardown (higiene de custos)

Boa notícia: nesta prática, o "teardown" foi **a própria prática** (deletar zumbis 😄). Sobre o
que criamos:

- ✅ **Budget `budget-ec2-mensal`** — não custa nada; **mantenha** (é proteção, não gasto).
- ✅ **Cost Anomaly Detection** — gratuito; **mantenha ligado**.
- ✅ **Cost allocation tags** — sem custo; mantenha ativas.
- ✅ Estimativa do Pricing Calculator — só um link, nada na conta.
- 🔥 Confirme que deletou (ou tagueou para revisão) os zumbis encontrados na Parte E.

> Este é o único módulo em que o teardown é **manter** as coisas: as travas de custo devem
> sobreviver ao curso.

---

## ✅ Checklist de conclusão do módulo

- [ ] Naveguei o Cost Explorer: agrupei por serviço, região e usage type, e sei qual foi o serviço
      mais caro do curso.
- [ ] Ativei cost allocation tags (e sei que não retroagem).
- [ ] Criei um budget filtrado por serviço com alertas em 80% real e 100% previsto.
- [ ] Ativei o Cost Anomaly Detection com monitor por serviço e assinatura de alerta.
- [ ] Estimei a arquitetura de referência no Pricing Calculator e comparei On-Demand vs. Savings Plan.
- [ ] Rodei a caça aos zumbis: volumes `available`, EIPs soltos, snapshots órfãos, logs sem retenção.
- [ ] Deletei (ou marquei para revisão) o que encontrei.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-17/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-17/`) e para o **Módulo 18 — Alta Disponibilidade & DR**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 17" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
