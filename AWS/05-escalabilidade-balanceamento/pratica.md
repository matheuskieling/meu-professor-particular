# Módulo 05 — Escalabilidade & Balanceamento (Prática Guiada)

> Objetivo desta prática: montar a arquitetura clássica de alta disponibilidade — **Launch Template
> → Auto Scaling Group (2 instâncias em 2 AZs) → ALB na frente** — ver o balanceamento acontecendo
> de verdade com `curl`, e **assistir ao ASG repor uma instância** que você mesmo vai derrubar.
>
> **Abordagem:** Console web primeiro (pra ver), CLI depois (pra fixar). Cada passo explica o *porquê*.
>
> ⏱️ Tempo estimado: 60–90 min.

---

## ⚠️ Antes de começar — custos (leia mesmo)

- **EC2 `t3.micro`:** dentro do Free Tier (750h/mês nos primeiros 12 meses). 2 instâncias por
  ~1h30 = ok. Fora do Free Tier: centavos.
- **ALB: NÃO é Free Tier de longo prazo.** Cobra **por hora de existência** (~US$ 0,0225/h em
  `us-east-1`) + LCUs. Pra esta prática (1–2h), o custo é de **centavos** — mas um ALB **esquecido
  ligado custa ~US$ 16/mês**. O teardown no fim é **obrigatório e rigoroso**.
- Faça a prática **inteira numa sessão** se puder. Se precisar parar no meio, **faça o teardown**
  e recrie depois (com a CLI é rápido).
- Região: **`us-east-1`**, como no resto do curso.
- Pré-requisito: a VPC default (ou a VPC do Módulo 03) com **subnets públicas em pelo menos 2 AZs**.

---

## Parte A — Security groups (Console)

Vamos criar dois SGs: um pro ALB (aberto pra internet) e um pras instâncias (aberto **só pro ALB**).

### Passo 1 — SG do ALB
1. Console → **EC2** → **Security Groups** → **Create security group**.
2. Nome: `m05-alb-sg` · Descrição: `ALB do modulo 05` · VPC: a default.
3. **Inbound:** HTTP (80) de `0.0.0.0/0`.
4. Crie.

### Passo 2 — SG das instâncias
1. **Create security group** → Nome: `m05-web-sg` · VPC: a mesma.
2. **Inbound:** HTTP (80) com **Source = `m05-alb-sg`** (digite o nome/ID do SG, não um CIDR!).
3. Crie.

> **Por quê:** referenciar o SG do ALB como origem garante que **só o ALB** alcança as instâncias.
> Ninguém acessa uma instância por fora — é o padrão correto. E lembre: health check falhando com
> app no ar geralmente é **este** SG errado.

---

## Parte B — Launch Template (Console)

### Passo 3 — Criar o template
1. **EC2** → **Launch Templates** → **Create launch template**.
2. Nome: `m05-web-lt` · Marque **Provide guidance to help me set up a template that I can use with EC2 Auto Scaling**.
3. **AMI:** Amazon Linux 2023 (x86_64). **Instance type:** `t3.micro`.
4. **Key pair:** opcional (não vamos precisar de SSH). **Subnet: não selecione** (quem decide é o ASG).
5. **Security group:** `m05-web-sg`.
6. Em **Advanced details → User data**, cole:

```bash
#!/bin/bash
dnf install -y nginx
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone)
echo "<h1>Ola do host $(hostname) na AZ $AZ</h1>" > /usr/share/nginx/html/index.html
systemctl enable --now nginx
```

7. Crie o template.

> **Por quê:** o user data instala o nginx e escreve uma página com o **hostname e a AZ** da
> instância. É assim que vamos *ver* o balanceamento: cada `curl` vai mostrar um host diferente.
> (O bloco do TOKEN é o IMDSv2 — o jeito atual e seguro de ler metadados da instância.)

---

## Parte C — Target group + ALB (Console)

### Passo 4 — Target group
1. **EC2** → **Target Groups** → **Create target group**.
2. Tipo: **Instances** · Nome: `m05-web-tg` · Protocolo: HTTP:80 · VPC: a mesma.
3. **Health check:** HTTP, path `/`. Em Advanced: healthy threshold 2, interval 15s (pra prática
   ficar ágil).
4. Crie **sem registrar targets** — quem vai registrar é o ASG.

### Passo 5 — Criar o ALB
1. **EC2** → **Load Balancers** → **Create load balancer** → **Application Load Balancer**.
2. Nome: `m05-alb` · Scheme: **Internet-facing** · IP: IPv4.
3. **Network mapping:** selecione a VPC e **duas subnets públicas em AZs diferentes** (ex.:
   `us-east-1a` e `us-east-1b`). ALB exige no mínimo 2 AZs.
4. **Security group:** `m05-alb-sg` (remova o default).
5. **Listener:** HTTP:80 → forward para `m05-web-tg`.
6. Crie. Ele fica `provisioning` por ~2 min. **Copie o DNS name** (algo como
   `m05-alb-123456.us-east-1.elb.amazonaws.com`).

---

## Parte D — Auto Scaling Group (Console)

### Passo 6 — Criar o ASG
1. **EC2** → **Auto Scaling Groups** → **Create Auto Scaling group**.
2. Nome: `m05-web-asg` · Launch template: `m05-web-lt` (versão Latest).
3. **Network:** a VPC e as **mesmas 2 subnets** do ALB.
4. **Load balancing:** **Attach to an existing load balancer** → escolha o target group `m05-web-tg`.
5. **Health checks:** marque **Turn on Elastic Load Balancing health checks**. Grace period: 90s.
6. **Group size:** desired **2**, min **2**, max **4**.
7. (Pule políticas de scaling por ora — a aula foca no mecanismo. Target tracking fica como bônus.)
8. Crie.

> **Por quê:** anexar o target group faz o registro/desregistro de instâncias ser automático.
> O health check ELB fecha o ciclo do auto-healing. O grace period dá tempo do user data terminar
> antes do ASG julgar a instância.

### Passo 7 — Ver a frota nascer
1. Na aba **Activity** do ASG: dois eventos "Launching a new EC2 instance".
2. Em **Target Groups → m05-web-tg → Targets**: as duas instâncias devem sair de `initial` para
   **`healthy`** em 1–3 min (nginx subindo + health checks passando).

---

## Parte E — Testar o balanceamento 🎉

### Passo 8 — curl repetido
No seu terminal (troque pelo DNS do seu ALB):

```bash
ALB=http://m05-alb-123456.us-east-1.elb.amazonaws.com
for i in $(seq 1 8); do curl -s $ALB; done
```

Você deve ver **hostnames (e AZs) alternando** entre as respostas — o ALB distribuindo em
round-robin entre as duas instâncias, em duas AZs. Isso é balanceamento + alta disponibilidade
funcionando de verdade.

### Passo 9 — Simular falha (a melhor parte)
1. **EC2 → Instances** → selecione **uma** das instâncias do ASG → **Instance state → Terminate**.
2. Rode o `for` do curl de novo: as respostas continuam vindo (**só do host sobrevivente** — zero
   downtime pro usuário).
3. Abra **Auto Scaling Groups → m05-web-asg → Activity**: o ASG detecta a perda e **lança uma
   substituta sozinho** pra voltar ao desired=2.
4. Aguarde 2–3 min e rode o curl de novo: **um hostname novo** aparece na rotação.

> Você acabou de presenciar o **auto-healing**: falha real, reposição automática, usuário nem viu.

---

## Parte F — Agora pela CLI (fixar)

Os mesmos objetos, agora inspecionados (e criáveis) por comando. Rode e interprete:

```bash
# Ver o launch template e sua versão
aws ec2 describe-launch-templates --query "LaunchTemplates[].{Nome:LaunchTemplateName,Versao:LatestVersionNumber}" --output table

# Ver o ASG: tamanhos, AZs, instâncias e health check
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names m05-web-asg \
  --query "AutoScalingGroups[].{Min:MinSize,Max:MaxSize,Desired:DesiredCapacity,AZs:AvailabilityZones,HC:HealthCheckType}"

# Ver a saúde dos targets (o que o ALB enxerga)
TG_ARN=$(aws elbv2 describe-target-groups --names m05-web-tg --query "TargetGroups[0].TargetGroupArn" --output text)
aws elbv2 describe-target-health --target-group-arn $TG_ARN \
  --query "TargetHealthDescriptions[].{Id:Target.Id,Estado:TargetHealth.State}" --output table

# Mudar o desired na marra (scale out manual) e ver a Activity
aws autoscaling set-desired-capacity --auto-scaling-group-name m05-web-asg --desired-capacity 3
aws autoscaling describe-scaling-activities --auto-scaling-group-name m05-web-asg --max-items 3 \
  --query "Activities[].{Status:StatusCode,Desc:Description}"
```

Depois do scale out, rode o curl de novo: **três** hostnames na rotação. Volte pra 2:

```bash
aws autoscaling set-desired-capacity --auto-scaling-group-name m05-web-asg --desired-capacity 2
```

> Repare no scale in: o target entra em `draining` no target group antes de morrer — é o
> **deregistration delay** deixando as conexões em andamento terminarem.

---

## Parte G — 🔥 TEARDOWN (obrigatório — o ALB cobra por hora!)

Ordem importa. Faça **agora**, não "depois":

```bash
# 1. ASG: zerar e deletar (termina as instâncias)
aws autoscaling update-auto-scaling-group --auto-scaling-group-name m05-web-asg --min-size 0 --desired-capacity 0
aws autoscaling delete-auto-scaling-group --auto-scaling-group-name m05-web-asg --force-delete

# 2. ALB
ALB_ARN=$(aws elbv2 describe-load-balancers --names m05-alb --query "LoadBalancers[0].LoadBalancerArn" --output text)
aws elbv2 delete-load-balancer --load-balancer-arn $ALB_ARN

# 3. Target group (só depois do ALB sumir; aguarde ~1 min)
TG_ARN=$(aws elbv2 describe-target-groups --names m05-web-tg --query "TargetGroups[0].TargetGroupArn" --output text)
aws elbv2 delete-target-group --target-group-arn $TG_ARN

# 4. Launch template
aws ec2 delete-launch-template --launch-template-name m05-web-lt

# 5. Security groups (depois que as instâncias terminarem)
aws ec2 delete-security-group --group-name m05-web-sg
aws ec2 delete-security-group --group-name m05-alb-sg
```

**Verificação final (tudo deve vir vazio/erro "not found"):**

```bash
aws elbv2 describe-load-balancers --names m05-alb
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names m05-web-asg --query "AutoScalingGroups"
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" --query "Reservations[].Instances[].InstanceId"
```

> ✅ Confirme também no Console: **Load Balancers vazio**, **ASGs vazio**, **Instances sem nada
> running**. ALB esquecido = ~US$ 16/mês. Não pule esta parte.

---

## ✅ Checklist de conclusão do módulo

- [ ] Security groups criados com o padrão "instância só aceita do SG do ALB".
- [ ] Launch Template com user data (nginx + hostname) criado.
- [ ] Target group e ALB (2 AZs) criados.
- [ ] ASG (min=2/desired=2/max=4) anexado ao target group, com health check ELB.
- [ ] Curl repetido mostrou hosts/AZs alternando (balanceamento visto ao vivo).
- [ ] Instância terminada na mão e **reposta automaticamente** pelo ASG.
- [ ] Scale out/in manual feito pela CLI (desired 3 → 2).
- [ ] **Teardown completo** — nenhum ALB, ASG ou instância viva.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-05/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-05/`) e para o **Módulo 06 — Storage: S3 & cia**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 5" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
