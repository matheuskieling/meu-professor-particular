# Módulo 18 — Alta Disponibilidade & Disaster Recovery (Teoria)

> Objetivo do módulo: aprender a projetar para a falha. Você vai dominar **RTO e RPO** (as duas
> métricas que governam tudo), entender **SLA composto**, separar **HA dentro da região** (multi-AZ)
> de **DR entre regiões**, conhecer as **4 estratégias de DR** em ordem de custo, e as ferramentas:
> **AWS Backup**, replicações (S3 CRR, réplicas cross-region, DynamoDB global tables) e
> **failover de DNS com Route 53**. Fecha com a filosofia do **chaos engineering**: testar a falha
> antes que ela te teste.

> 🧠 Mantra do módulo (Werner Vogels, CTO da Amazon): **"Everything fails, all the time."**
> A pergunta nunca é *se* vai falhar — é *o que acontece quando* falhar.

---

## 1. RTO e RPO: as duas perguntas que definem tudo

Antes de escolher qualquer tecnologia, o negócio precisa responder duas perguntas:

### RTO — Recovery Time Objective ("quanto tempo posso ficar FORA DO AR?")
O tempo máximo aceitável entre a falha e o serviço voltar a operar. Mede **indisponibilidade**.

### RPO — Recovery Point Objective ("quantos DADOS posso perder?")
A janela máxima aceitável de dados perdidos, medida em **tempo antes da falha**. Se seu último
backup foi há 6 horas e o banco explodiu agora, você perdeu 6 horas de dados → seu RPO real é 6h.

```
            RPO                      RTO
   ◄─────────────────────►◄─────────────────────►
───┬─────────────────────┬─────────────────────┬───► tempo
último backup          FALHA               serviço volta
(dados até aqui        💥                  a operar
 estão salvos)
   └── dados perdidos ──┘└──── fora do ar ─────┘
```

**Exemplos numéricos** (grave estes):

| Sistema | RTO | RPO | Leitura |
|---------|-----|-----|---------|
| Blog pessoal | 24h | 24h | Restaurar backup diário amanhã? Ok. |
| E-commerce médio | 1h | 5 min | Até 1h fora; perder no máx. 5 min de pedidos. |
| Pagamentos/banco | segundos | ~0 | Nem cair, nem perder uma transação. |

Regras de ouro:
- **RTO/RPO menores = custo maior.** Sempre. Cortar RTO de 1h para 1min pode multiplicar o custo
  por 10. Por isso a decisão é **do negócio**, não só da engenharia: quanto custa 1h fora do ar?
- RPO é definido por **frequência de backup/replicação**; RTO, pela **velocidade de restauração
  e failover**. São alavancas diferentes.
- **RTO/RPO declarados no papel valem zero** até serem testados. (Voltamos nisso no chaos engineering.)

---

## 2. SLA da AWS vs. SLA da sua aplicação

Cada serviço AWS publica um **SLA** (Service Level Agreement): o compromisso de disponibilidade,
com créditos se descumprido. Exemplos: EC2 (região) 99,99%, ALB 99,99%, RDS Multi-AZ 99,95%,
S3 99,9% (Standard), Route 53 100% (o único!).

A pegadinha: sua aplicação **depende de vários serviços em série** — e disponibilidades em série
**se multiplicam**:

```
App = ALB (99,99%) × EC2 (99,99%) × RDS Multi-AZ (99,95%)
    ≈ 99,93%  →  ~6h de indisponibilidade "aceitável" por ano
```

Ou seja: **seu SLA composto é sempre PIOR que o do pior componente.** Cada dependência em série
derruba o total. Consequências práticas:

- Quer melhorar a disponibilidade? Coloque componentes **em paralelo** (redundância), não em série.
  Dois componentes de 99% em paralelo (qualquer um serve) ≈ 99,99%.
- O SLA da AWS te dá **créditos**, não te devolve os clientes perdidos. SLA é contrato financeiro,
  não garantia física.
- Um número mnemônico: 99,9% = ~8,7 h/ano fora; 99,99% = ~52 min/ano; 99,999% = ~5 min/ano.

---

## 3. HA dentro da região vs. DR entre regiões

Duas disciplinas diferentes, com ferramentas diferentes — não misture:

### Alta Disponibilidade (HA) = sobreviver a falhas COMUNS, automaticamente
Falha de instância, de processo, de **uma AZ**. Resolve-se **dentro da região**, com redundância
multi-AZ — e você já construiu tudo isso no curso:

- **ALB + Auto Scaling Group em 2+ AZs** (Módulo 05): instância morre → health check tira do
  balanceador → ASG repõe. Ninguém percebe.
- **RDS Multi-AZ** (Módulo 07): réplica síncrona em outra AZ; failover automático em ~1–2 min
  (o DNS do endpoint aponta pra standby). **Atenção:** Multi-AZ é disponibilidade, não performance
  — a standby não serve leitura (diferente de read replica!).
- **EFS / S3 / DynamoDB / Aurora**: já são multi-AZ **por design** — o dever de casa vem pronto.

### Disaster Recovery (DR) = sobreviver a desastres RAROS, com plano
Região inteira indisponível, desastre natural, **erro humano catastrófico** (deletar o banco de
produção — mais comum que terremoto! 😅), ransomware. Resolve-se **entre regiões** (ou pelo menos
com backups isolados), e quase sempre envolve **decisão + procedimento** (runbook), não só automação.

> 💡 **Regra mental:** HA é o **para-choque** (absorve batidas do dia a dia, automático);
> DR é o **seguro do carro** (evento raro, tem franquia/custo, exige acionar um processo).
> Multi-AZ **não é** DR: se o erro humano deletar a tabela, ele deleta nas duas AZs — sincronizadinho.

---

## 4. As 4 estratégias de DR (em ordem de custo)

O espectro clássico da AWS, do mais barato/lento ao mais caro/rápido:

| Estratégia | Como funciona | RTO típico | RPO típico | Custo relativo |
|-----------|---------------|-----------|-----------|----------------|
| **1. Backup & Restore** | Só backups na região secundária; reconstrói tudo quando precisar | horas a 24h+ | horas (última cópia) | 💰 (só storage) |
| **2. Pilot Light** | Núcleo mínimo sempre ligado no destino (dados replicando, ex.: banco); resto desligado/IaC | dezenas de min a horas | minutos | 💰💰 |
| **3. Warm Standby** | Cópia **funcional porém reduzida** do ambiente rodando no destino; escala na virada | minutos | segundos a minutos | 💰💰💰 |
| **4. Multi-site Active/Active** | Produção completa em 2+ regiões, ambas servindo tráfego | ~zero (segundos) | ~zero | 💰💰💰💰 |

Detalhes que caem em prova (e na vida):

1. **Backup & Restore** — o mínimo aceitável para *qualquer* sistema. Barato, mas o RTO depende de
   reconstruir infra do zero (**IaC do Módulo 11 é o que torna isso viável** — restaurar na mão,
   sem código, leva dias). Cobre também o caso ransomware/erro humano (backup é imutável no tempo).
2. **Pilot Light** — a "chama piloto" do aquecedor: os **dados** replicam continuamente (é o que
   não dá pra recriar!), e a infra de aplicação existe só como código/AMIs, pronta pra acender.
   RPO bom (dados quase em dia), RTO médio (subir a infra leva tempo).
3. **Warm Standby** — tudo já **ligado e funcionando** no destino, mas em tamanho mínimo (ex.: 1
   instância em vez de 10). A virada é: apontar o DNS e escalar. RTO de minutos.
4. **Active/Active** — as duas regiões servem tráfego o tempo todo (Route 53 com roteamento
   latency/weighted). Falhou uma, a outra absorve. Requer o problema mais difícil: **dados
   escrevíveis em duas regiões** (DynamoDB global tables, Aurora Global Database) e resolução de
   conflitos. Reservado a quem realmente não pode cair.

> 🎯 A escolha vem **do RTO/RPO do negócio**, nunca da vaidade técnica. A maioria das empresas
> vive muito bem com backup & restore + um bom runbook testado.

---

## 5. AWS Backup: backups centralizados como política

Fazer backup "na mão" por serviço (snapshot de EBS aqui, snapshot de RDS ali, export de DynamoDB
acolá) não escala e ninguém audita. O **AWS Backup** centraliza:

- **Backup plan**: a política — frequência (ex.: diário 3h), janela, **retenção** (ex.: 35 dias),
  transição pra cold storage. Um plano, muitos recursos.
- **Atribuição de recursos**: você associa recursos ao plano **por tag** (ex.: tudo com
  `Backup=diario`) ou por ARN. Tag nova entra no plano sozinha — política, não checklist.
- **Backup vault**: onde os **recovery points** ficam guardados, com criptografia e política de
  acesso própria. **Vault Lock** (WORM) impede deleção até de admins — antídoto anti-ransomware.
- **Cross-region copy**: o plano pode copiar automaticamente cada backup pra outra região — sua
  estratégia backup & restore de DR em um checkbox.
- Serviços suportados: EBS, EC2 (AMI), RDS/Aurora, DynamoDB, EFS, S3, FSx, entre outros.

> ⚠️ **Backup não testado é uma esperança, não um backup.** A métrica que importa não é "o job
> rodou", é "**eu consegui restaurar** e o RTO/RPO reais bateram com os prometidos". Na prática
> deste módulo você vai restaurar de verdade.

---

## 6. Replicação contínua: encurtando o RPO

Backup te dá RPO de horas. Pra RPO de segundos/minutos, é preciso **replicar continuamente**:

- **S3 Cross-Region Replication (CRR)**: replica objetos automaticamente pra um bucket em outra
  região. Requer **versionamento habilitado nos dois buckets** e uma role IAM. Replica **objetos
  novos** a partir da ativação (pro passado, existe Batch Replication). Assíncrona — RPO de
  segundos a minutos. (Tem a irmã SRR, same-region, pra outros casos.)
- **RDS read replica cross-region**: réplica **assíncrona** de leitura em outra região. Em
  desastre, você **promove** a réplica a banco independente (ação manual/scriptada, minutos).
  É o coração de um pilot light/warm standby. Não confunda os dois eixos do RDS:
  **Multi-AZ = HA síncrona, failover automático, mesma região** vs. **read replica = assíncrona,
  serve leitura, pode ser cross-region, promoção manual**.
- **DynamoDB Global Tables**: replicação **multi-ativa** — todas as regiões aceitam **escrita**,
  replicação típica em ~1 segundo, resolução de conflito *last writer wins*. É o dado pronto pra
  active/active sem você operar nada.
- (Menção honrosa: **Aurora Global Database** — réplica cross-region com lag <1s e promoção em ~1 min.)

---

## 7. Route 53 failover: a chave geral da virada

Replicou dados, tem ambiente no destino... falta a pergunta final: **como o tráfego muda de região?**
Resposta: DNS. O **Route 53** (Módulo 14) tem a política de roteamento **Failover**:

- Registro **primário** (ex.: ALB em `us-east-1`) com um **health check** associado.
- Registro **secundário** (ex.: ALB em `us-west-2`, ou uma página estática de "estamos em
  manutenção" no S3/CloudFront — melhor que erro de conexão!).
- O health check testa o endpoint de fora (frota global de verificadores da AWS, por
  HTTP/HTTPS/TCP, checando a cada 30s ou 10s). **Falhou N vezes → o Route 53 passa a responder o
  secundário.** Automático.

Detalhes de quem já se queimou:
- **TTL baixo** no registro (30–60s), senão clientes seguram o IP antigo em cache e sua "virada
  automática" leva uma eternidade.
- Health check deve testar algo **significativo** (ex.: `/health` que toca o banco), não só
  "porta 80 abre" — senão você faz failover pro nada ou deixa de fazer quando deveria.
- Health check custa **~US$ 0,50/mês** (endpoint AWS; um pouco mais para opções extras). Baratíssimo
  pra produção; no curso, **apagamos no teardown**.
- Failover routing também funciona **dentro** de uma arquitetura DR manual: o health check pode
  ser só o gatilho de alarme, e a virada, decisão humana via runbook. Automatizar a virada de
  região inteira é decisão séria (falso positivo = failover desnecessário, com dores próprias).

---

## 8. Chaos engineering: teste a falha antes que ela te teste

A última peça é cultural. **Chaos engineering** é a disciplina de **injetar falhas de propósito,
de forma controlada**, pra descobrir as fraquezas antes do desastre real. Nasceu na Netflix
(Chaos Monkey, que matava instâncias aleatórias em produção) e virou prática de mercado.

O método científico da coisa:
1. **Hipótese**: "se uma instância do ASG morrer, os usuários não percebem."
2. **Experimento controlado**: mate uma instância (em horário controlado, com raio de explosão
   limitado, com botão de parada).
3. **Observe** (dashboards e alarmes do Módulo 12 — sem observabilidade não há chaos engineering,
   há só vandalismo 😄).
4. **Corrija** o que surpreendeu; **repita** — e aumente a dose (uma AZ, uma dependência, a região).

Na AWS, o serviço gerenciado é o **AWS FIS (Fault Injection Service)**: experimentos declarativos
(matar instâncias, estressar CPU, injetar latência de rede, simular indisponibilidade de AZ) com
condições de parada automáticas. Não vamos operá-lo neste curso, mas o princípio, sim — na prática,
seu "chaos" será um **tabletop exercise** (simulação verbal de desastres) e, no projeto final,
uma falha real injetada à mão.

> 🎯 **GameDays**: exercícios agendados em que o time simula um desastre e executa o runbook.
> O objetivo não é passar, é **achar o que falha no plano** — com café na mão, e não às 3h da manhã.

---

## 9. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| RTO | Tempo máximo aceitável fora do ar (mede indisponibilidade). |
| RPO | Janela máxima aceitável de dados perdidos (mede perda de dados). |
| SLA | Compromisso contratual de disponibilidade; em série, os SLAs se multiplicam (pioram). |
| HA (multi-AZ) | Sobreviver a falhas comuns automaticamente, dentro da região. |
| DR (multi-região) | Sobreviver a desastres raros, com plano e runbook. |
| Backup & Restore | DR mais barato: só backups no destino; RTO de horas. |
| Pilot Light | Dados replicando + infra mínima desligada no destino, pronta pra "acender". |
| Warm Standby | Cópia funcional reduzida rodando no destino; escala na virada. |
| Active/Active | Duas+ regiões servindo tráfego; RTO/RPO ~zero; custo máximo. |
| AWS Backup | Backups centralizados por política (planos, vaults, cross-region copy, Vault Lock). |
| Recovery point | Um backup restaurável guardado num vault. |
| S3 CRR | Replicação automática de objetos entre regiões (requer versionamento). |
| Global Tables | DynamoDB multi-ativo entre regiões, replicação ~1s. |
| Failover routing | Route 53 responde o secundário quando o health check do primário falha. |
| Chaos engineering | Injetar falhas controladas pra achar fraquezas antes do desastre real (AWS FIS). |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Defina RTO e RPO **com suas palavras** e dê um exemplo numérico de cada pra um e-commerce.
2. Backup diário às 3h; o banco corrompeu às 15h. Qual o RPO **real** desse incidente?
3. Por que uma aplicação ALB→EC2→RDS tem SLA composto **pior** que 99,95%, mesmo com todos os
   componentes acima disso?
4. Por que RDS Multi-AZ **não** te protege de um `DROP TABLE` acidental em produção?
5. Ordene as 4 estratégias de DR por custo e diga o RTO típico de cada.
6. O que o S3 CRR exige nos dois buckets, e o que acontece com objetos que já existiam antes de ativar?
7. Num failover de DNS, por que um TTL alto sabota seu RTO?
8. Qual é a diferença entre chaos engineering e "derrubar produção sem avisar"? 😄

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
