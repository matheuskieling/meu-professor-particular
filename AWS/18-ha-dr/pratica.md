# Módulo 18 — Alta Disponibilidade & Disaster Recovery (Prática Guiada)

> Objetivo desta prática: **provar RPO e RTO na prática**, não só na teoria. Você vai criar um
> plano no **AWS Backup**, rodar um backup on-demand e **restaurar de verdade**; configurar
> **S3 Cross-Region Replication** e ver um objeto atravessar regiões; montar um **failover DNS**
> com health check do Route 53; e fechar com um **tabletop exercise** de cenários de desastre.
>
> **Abordagem:** Console primeiro (pra ver), CLI depois (pra fixar).
>
> ⏱️ Tempo estimado: 90–120 min. 💵 Custo: **centavos** se fizer o teardown no mesmo dia:
> volume EBS pequeno + recovery points (GB-mês fracionado), 2 buckets S3 com objetos mínimos,
> health check do Route 53 (**~US$ 0,50/mês, pró-rata — APAGAR no teardown**).

---

## ⚠️ Antes de começar — leia isto

- Trabalharemos em **duas regiões**: `us-east-1` (primária) e `us-west-2` (secundária/DR).
  Atenção redobrada ao **seletor de região** — metade dos recursos vai estar "na outra".
- Tudo que criarmos aqui entra no **teardown obrigatório** do final — inclusive os **recovery
  points dentro do vault** (backup deletado à parte do plano!) e o **health check** do Route 53.
- Se você ainda tem o alerta de billing do Módulo 01/17 ativo (deveria!), ele é sua rede de segurança.

---

## Parte A — AWS Backup: plano, backup on-demand e RESTAURAÇÃO (Console)

### Passo 1 — Criar um recurso pra proteger
Precisamos de algo pra fazer backup. Um volume EBS pequeno serve:
1. Console (`us-east-1`) → **EC2 → Volumes → Create volume**: tipo **gp3**, **1 GiB**,
   AZ `us-east-1a`. Tag: `Name=vol-dr-lab` e `Backup=lab`.
2. (Alternativa: se ainda tiver a tabela DynamoDB de módulos anteriores, pode usá-la como alvo.)

### Passo 2 — Criar o backup plan
1. Console → **AWS Backup** → **Backup plans → Create backup plan** → **Build a new plan**.
2. Nome: `plano-dr-lab`. Regra: nome `diario`, frequência **Daily**, janela padrão,
   retenção **7 dias**, vault **Default** (ou crie `vault-dr-lab`).
3. (Observe a opção **Copy to destination** — é aqui que um plano real copiaria cada backup pra
   `us-west-2`. Não vamos ativar no lab pra não dobrar recovery points, mas registre onde fica.)
4. **Assign resources**: nome `recursos-lab`, método **por tag**: `Backup = lab`. Confirme.

> **Por quê por tag:** recurso novo com a tag entra no plano automaticamente. Backup vira
> **política**, não checklist manual.

### Passo 3 — Backup on-demand (não vamos esperar até amanhã)
1. **AWS Backup → Protected resources → Create on-demand backup**.
2. Tipo **EBS**, selecione `vol-dr-lab`, retenção **1 semana**, vault do plano. **Create**.
3. Acompanhe em **Jobs → Backup jobs** até `Completed` (alguns minutos).
4. Veja o **recovery point** no vault: isso é seu RPO materializado — "os dados até *este momento*
   estão salvos".

### Passo 4 — RESTAURAR (a parte que quase ninguém testa)
1. No vault, selecione o recovery point → **Restore**.
2. Restaure como **novo volume** na mesma AZ. Acompanhe em **Jobs → Restore jobs**.
3. Quando completar, confira em EC2 → Volumes: há um **novo volume** vindo do backup.
4. **Cronometre**: quanto tempo levou do clique "Restore" ao volume disponível? **Esse é seu RTO
   real** (de restauração de um recurso). Anote — a pergunta "seu backup restaura em quanto
   tempo?" agora tem resposta medida, não chutada.

> 🎯 Você acabou de provar o ciclo completo: **backup → recovery point → restore funcionando**.
> A maioria das empresas só descobre que o passo 4 falha durante o desastre.

---

## Parte B — S3 Cross-Region Replication (Console + CLI)

### Passo 5 — Criar os dois buckets (com versionamento!)
```bash
SUFIXO=$RANDOM   # bucket name é global; sufixo evita colisão
aws s3api create-bucket --bucket dr-lab-primario-$SUFIXO --region us-east-1
aws s3api create-bucket --bucket dr-lab-replica-$SUFIXO --region us-west-2 \
  --create-bucket-configuration LocationConstraint=us-west-2

# CRR EXIGE versionamento nos DOIS lados
aws s3api put-bucket-versioning --bucket dr-lab-primario-$SUFIXO \
  --versioning-configuration Status=Enabled
aws s3api put-bucket-versioning --bucket dr-lab-replica-$SUFIXO \
  --versioning-configuration Status=Enabled
```

### Passo 6 — Configurar a replicação (Console, mais didático)
1. Console → S3 → bucket `dr-lab-primario-...` → **Management → Replication rules →
   Create replication rule**.
2. Nome: `crr-lab`, escopo **Apply to all objects**.
3. Destino: **bucket em outra região** → `dr-lab-replica-...` (em `us-west-2`).
4. IAM role: **Create new role** (o console cria a role que autoriza o S3 a replicar).
5. Salve. Se perguntar sobre replicar objetos existentes (Batch Replication), responda **No** —
   queremos ver que **só objetos novos** replicam.

### Passo 7 — Ver a mágica acontecer
```bash
echo "sobrevivi ao desastre $(date)" > prova-de-vida.txt
aws s3 cp prova-de-vida.txt s3://dr-lab-primario-$SUFIXO/

# aguarde alguns segundos/minutos e confira o OUTRO LADO DO PAÍS:
aws s3 ls s3://dr-lab-replica-$SUFIXO/
aws s3api head-object --bucket dr-lab-replica-$SUFIXO --key prova-de-vida.txt \
  --query ReplicationStatus
```
O `ReplicationStatus` no destino vem como `REPLICA`. Seu objeto agora existe em duas regiões
separadas por milhares de km — **RPO de segundos, sem você operar nada**.

---

## Parte C — Failover DNS com Route 53 (Console)

> ⚠️ **Custo:** o health check custa **~US$ 0,50/mês** (cobrado pró-rata). Criado agora e apagado
> no teardown de hoje = centavos. **Não esqueça dele.**
> 💡 Se você **não** tem uma hosted zone/domínio (Módulo 14), faça só os passos do health check
> (8–9) — o conceito de failover fica montado "na cabeça" e o custo é o mesmo.

### Passo 8 — Criar um health check
1. Console → **Route 53 → Health checks → Create health check**.
2. Nome: `hc-primario-lab`. Tipo **Endpoint**, protocolo **HTTPS**, domínio de algo seu que está
   no ar (ex.: o site estático/CloudFront do Módulo 14 — ou até `example.com` só pra ver funcionar).
3. Avançado: intervalo **30s** (padrão), 3 falhas pro unhealthy. Crie.
4. Aguarde e veja o status ficar **Healthy** (a frota global de verificadores da AWS está,
   literalmente, testando seu endpoint agora).

### Passo 9 — Ver o failover "acontecer" (simulação segura)
1. Edite o health check e troque o caminho/porta por algo que **não existe** (ex.: porta `8443`
   ou caminho `/nao-existe-403`). Aguarde ~2 min → status **Unhealthy**. Em produção, é ESTE
   sinal que dispararia a troca de resposta do DNS.
2. Volte a configuração correta → **Healthy** de novo. Você acabou de assistir ao gatilho do
   failover dos dois lados.

### Passo 10 — (Opcional, se tem hosted zone) Registros failover
1. Na hosted zone, crie **dois registros** com o mesmo nome (ex.: `app.seudominio.com`):
   - Registro 1 — routing policy **Failover: Primary**, associado ao `hc-primario-lab`,
     apontando pro seu endpoint primário. **TTL 60**.
   - Registro 2 — **Failover: Secondary**, apontando pro "plano B" (ex.: endpoint alternativo ou
     página estática em S3/CloudFront de "em manutenção"). **TTL 60**.
2. Quebre o health check de novo (passo 9) e faça `dig app.seudominio.com` antes/depois: a
   resposta troca pro secundário. **Esse é o mecanismo da virada de região.**
3. Conserte o health check e delete os dois registros de teste.

> 🎯 Conecte com a teoria: TTL 60 significa que clientes seguram a resposta antiga por até 1 min —
> parte do seu **RTO**. TTL de 24h aqui destruiria qualquer plano de failover.

---

## Parte D — Tabletop exercise: o desastre é verbal (com o Claude)

Sem console agora. Peça pro Claude: **"me aplique o tabletop do módulo 18"**. Ele vai propor
cenários e você responde **(a)** qual estratégia de DR resolve, **(b)** o RTO/RPO resultante e
**(c)** os primeiros 3 passos do runbook. Exemplos do que vem:

1. Estagiário rodou `DROP TABLE pedidos` na produção às 14h. Backup diário às 3h + RDS com PITR.
   O que dá pra recuperar, e como Multi-AZ te ajudou aqui? (Spoiler: não ajudou. 😬)
2. `us-east-1` fora do ar (acontece!). Sua app: ALB+ASG+RDS, tudo single-region, IaC no Git,
   backups copiados pra `us-west-2`. RTO/RPO estimados? Passo a passo da reconstrução?
3. O negócio agora exige RTO 15 min / RPO 1 min com orçamento limitado. Qual estratégia e quais
   peças AWS (dica: réplica cross-region + warm standby + failover DNS)?
4. Ransomware criptografou os dados E o atacante tem credenciais de admin. Por que backups na
   mesma conta/região são insuficientes, e o que Vault Lock/cross-account muda?

Responder bem esses 4 vale mais que qualquer clique de console — DR é 20% tecnologia, 80% plano.

---

## Parte E — 🔥 Teardown (OBRIGATÓRIO — tem recurso cobrando!)

Na ordem, em `us-east-1` salvo indicação:

```bash
# 1. Recovery points (o plano NÃO apaga backups já feitos!)
#    Console: AWS Backup → Backup vaults → (seu vault) → selecionar recovery points → Delete
#    (na CLI: aws backup list-recovery-points-by-backup-vault / delete-recovery-point)

# 2. Backup plan (remova antes a atribuição de recursos)
#    Console: AWS Backup → Backup plans → plano-dr-lab → deletar resource assignment → Delete plan

# 3. Volumes EBS do lab (o original E o restaurado!)
aws ec2 describe-volumes --filters Name=tag:Name,Values=vol-dr-lab \
  --query "Volumes[].VolumeId" --output text
aws ec2 delete-volume --volume-id vol-XXXX   # repita para cada um (original + restaurado)

# 4. Buckets S3 (versionados: precisa esvaziar TODAS as versões antes)
#    Console é mais simples: bucket → Empty (confirma) → Delete. Para os DOIS buckets.
#    (regra de replicação morre junto com o bucket primário)

# 5. Health check do Route 53 (o ~US$0,50/mês!)
aws route53 list-health-checks --query "HealthChecks[].{Id:Id}" --output table
aws route53 delete-health-check --health-check-id XXXX

# 6. (Se fez o passo 10) confirme que os registros failover de teste foram deletados
```

### Verificação final
- [ ] Vault sem recovery points; plano deletado.
- [ ] Nenhum volume `vol-dr-lab` (nem o restaurado) em EC2 → Volumes.
- [ ] Os dois buckets `dr-lab-*` não existem mais (checar `us-east-1` **e** `us-west-2`).
- [ ] Zero health checks no Route 53.
- [ ] Passada rápida no Cost Explorer amanhã pra confirmar (hábito do Módulo 17 😉).

---

## ✅ Checklist de conclusão do módulo

- [ ] Criei um backup plan com regra, retenção e atribuição por tag.
- [ ] Rodei um backup on-demand e vi o recovery point no vault.
- [ ] **Restaurei** o backup e cronometrei meu RTO real de restauração.
- [ ] Configurei S3 CRR (com versionamento) e vi um objeto replicar pra outra região.
- [ ] Criei um health check do Route 53, vi Healthy→Unhealthy→Healthy e entendi o gatilho do failover.
- [ ] Sei explicar por que TTL alto sabota o RTO de um failover DNS.
- [ ] Respondi os 4 cenários do tabletop com estratégia, RTO/RPO e primeiros passos.
- [ ] **Teardown completo** — inclusive recovery points e health check.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-18/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-18/`) e para o grand finale: **Módulo 19 — Projeto Final (Capstone)**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 18" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
