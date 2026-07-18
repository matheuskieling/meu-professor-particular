# Módulo 04 — Compute: EC2 (Prática Guiada)

> Objetivo desta prática: lançar uma **t3.micro** com **user data** instalando nginx, acessar
> por **SSH**, explorar o **metadata (IMDSv2)**, criar um **snapshot** do disco — e no fim
> **terminar tudo com verificação** de que nada ficou cobrando. Console primeiro, depois os
> mesmos passos via CLI.
>
> ⏱️ Tempo estimado: 60–90 min. 💵 Custo: **US$ 0 dentro do Free Tier** (750h/mês de t3.micro,
> 30 GB de EBS, IP público junto da instância — nos 12 meses). Fora do Free Tier, uma t3.micro
> ligada custa ~US$ 0,01/h: centavos pra esta prática, **desde que o teardown seja feito**.
> O snapshot (poucos GB por algumas horas) custa ≈ zero.

---

## ⚠️ Antes de começar

- Pré-requisitos: Módulos 01–03 completos. Vamos usar a **default VPC** pra simplificar (uma
  instância de teste, exposta só nas portas certas — aceitável; você já sabe montar a VPC
  customizada e vamos juntá-las no Módulo 05).
- Região: **us-east-1** em tudo.
- A chave `.pem` vai pra `~/.ssh/`, **nunca** pro repositório.
- ⚠️ **Regra do módulo:** esta prática só termina no **terminate + verificação**. Instância
  "parada pra depois" continua cobrando EBS (e vira EIP/volume esquecido). Se quiser refazer,
  relance — user data reconstrói tudo em 1 minuto (essa é a beleza).

---

## Parte A — Lançar a instância (Console)

### Passo 1 — Criar a key pair
1. Console → **EC2** → **Key pairs** (menu lateral, em Network & Security) → **Create key pair**.
2. Name: `curso-key` · Type: **ED25519** · Format: **.pem** → **Create**.
3. O navegador baixa `curso-key.pem`. Mova e tranque:
   ```bash
   mv ~/Downloads/curso-key.pem ~/.ssh/
   chmod 400 ~/.ssh/curso-key.pem
   ```

> **Por quê `chmod 400`:** o SSH recusa chaves legíveis por outros usuários ("UNPROTECTED
> PRIVATE KEY FILE"). E lembre: a AWS **não guarda** cópia da privada — perdeu, era.

### Passo 2 — Launch instance
1. EC2 → **Instances** → **Launch instances**.
2. Name: `curso-web`.
3. **AMI:** Amazon Linux 2023 (default, Free tier eligible). Arquitetura: **64-bit (x86)**.
4. **Instance type:** `t3.micro` (confira o selo *Free tier eligible*).
5. **Key pair:** `curso-key`.
6. **Network settings** → **Edit**:
   - VPC: a **default**; Subnet: qualquer; **Auto-assign public IP: Enable**.
   - **Create security group**: name `curso-sg-ec2`;
     - SSH (22) → Source: **My IP**;
     - HTTP (80) → Source: `0.0.0.0/0`.
7. **Storage:** 8 GB **gp3** (confirme que é gp3, o padrão atual).

### Passo 3 — User data (antes de lançar!)
1. Expanda **Advanced details** → role até **User data** e cole:
   ```bash
   #!/bin/bash
   dnf update -y
   dnf install -y nginx
   systemctl enable --now nginx
   TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
   AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone)
   echo "<h1>Curso AWS — Módulo 04</h1><p>Servida por $(hostname) na AZ $AZ</p>" > /usr/share/nginx/html/index.html
   ```
2. Ainda em Advanced details, confira **Metadata version: V2 only (token required)** — é o
   default atual; deixe assim.
3. **Launch instance**. 🚀

> **O que vai acontecer:** a instância nasce, o cloud-init executa seu script como root,
> instala o nginx e monta uma página que **consulta o próprio metadata via IMDSv2**. Zero
> intervenção manual.

### Passo 4 — Ver a página no ar
1. Instances → `curso-web` → espere **Instance state: Running** e **Status checks: 2/2 passed**
   (~2 min; o user data pode levar mais 1–2 min após o running).
2. Copie o **Public IPv4 address** e abra `http://<ip>` no navegador (**http**, não https —
   não configuramos TLS).
3. Deve aparecer: *"Curso AWS — Módulo 04 / Servida por ... na AZ us-east-1x"*. 🎉

> Não abriu? Checklist do Módulo 03: instância running? SG com porta 80 aberta? IP público
> existe? Você digitou `http://`? (E o user data terminou? — veja o log no passo 6.)

---

## Parte B — SSH, metadata e snapshot (Console + terminal)

### Passo 5 — Conectar via SSH
```bash
ssh -i ~/.ssh/curso-key.pem ec2-user@<IP-PUBLICO>
```
- Primeira vez: confirme o fingerprint (`yes`).
- Prompt `[ec2-user@ip-10-...]$` = **você está dentro do seu servidor na AWS.**

> Usuário `ec2-user` é o padrão do Amazon Linux (Ubuntu usa `ubuntu`). Se der *Permission
> denied*: chave errada, usuário errado ou `chmod` não feito. *Timeout*: porta 22 não liberada
> pro seu IP atual no SG.

### Passo 6 — Explorar a instância por dentro
Dentro da sessão SSH:
```bash
# o nginx está mesmo rodando?
systemctl status nginx --no-pager

# o log do user data (SEMPRE o primeiro lugar quando o bootstrap "não funcionou")
sudo tail -30 /var/log/cloud-init-output.log

# IMDSv2 na prática — sem token, a resposta é 401:
curl -s -o /dev/null -w "%{http_code}\n" http://169.254.169.254/latest/meta-data/instance-id

# com token:
TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id; echo
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-type; echo
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4; echo
```
Saia com `exit`.

> O `401` sem token é o **IMDSv2** protegendo o metadata — é exatamente o que barra o ataque
> SSRF que discutimos na teoria. E se houvesse uma IAM role anexada, seria em
> `meta-data/iam/security-credentials/` que a CLI interna buscaria as credenciais temporárias.

### Passo 7 — Criar um snapshot do volume
1. Console → EC2 → **Volumes**: veja o volume de 8 GB gp3 da instância (repare na **AZ** dele
   e no **Delete on termination: Yes** na aba da instância).
2. Selecione o volume → **Actions → Create snapshot** → description `curso-snapshot-web` → criar.
3. **Snapshots** (menu lateral): acompanhe até **Status: Completed**.

> Snapshot = backup **incremental** do volume, guardado no S3. Dele você poderia criar um
> volume novo em **outra AZ**, ou uma AMI sua. Cobra ~US$ 0,05/GB·mês — o nosso, de poucos GB
> por algumas horas, custa ≈ nada (e morre no teardown).

### Passo 8 — Stop vs. start (sentir o ciclo de vida)
1. Instances → `curso-web` → **Instance state → Stop instance**. Aguarde **Stopped**.
2. Observe: o **Public IPv4 sumiu**; o volume EBS continua em **Volumes** (👉 **isso** continua
   cobrando numa instância parada).
3. **Start instance** → repare que voltou com **OUTRO IP público** (é pra isso que serviria um
   Elastic IP — que **não** vamos alocar: EIP ocioso cobra, e nosso servidor é descartável).
4. A página web voltou no IP novo? (O nginx sobe sozinho — `systemctl enable` no user data.)

---

## Parte C — Repetir via CLI

Termine a instância do Console antes (**Instance state → Terminate**) ou deixe pra terminar as
duas no teardown — só não esqueça. Vamos relançar tudo por comandos:

### Passo 9 — Descobrir a AMI mais recente (sem caçar ID no console)
```bash
AMI_ID=$(aws ssm get-parameter \
  --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query Parameter.Value --output text)
echo $AMI_ID
```
> A AWS publica a AMI atual num **parâmetro público do SSM** — o jeito reproduzível de sempre
> pegar a última, em qualquer região.

### Passo 10 — Security group + user data
```bash
VPC_ID=$(aws ec2 describe-vpcs --filters Name=is-default,Values=true \
  --query "Vpcs[0].VpcId" --output text)

SG_ID=$(aws ec2 create-security-group --vpc-id $VPC_ID \
  --group-name curso-sg-ec2-cli --description "EC2 do curso (CLI)" \
  --query GroupId --output text)

MEU_IP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr ${MEU_IP}/32
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0

cat > /tmp/userdata.sh <<'EOF'
#!/bin/bash
dnf update -y
dnf install -y nginx
systemctl enable --now nginx
echo "<h1>Curso AWS - M04 via CLI</h1>" > /usr/share/nginx/html/index.html
EOF
```

### Passo 11 — Lançar a instância
```bash
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.micro \
  --key-name curso-key \
  --security-group-ids $SG_ID \
  --associate-public-ip-address \
  --user-data file:///tmp/userdata.sh \
  --metadata-options "HttpTokens=required,HttpEndpoint=enabled" \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=curso-web-cli}]' \
  --query "Instances[0].InstanceId" --output text)
echo $INSTANCE_ID

# esperar ficar running e pegar o IP:
aws ec2 wait instance-running --instance-ids $INSTANCE_ID
IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
  --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
echo "http://$IP"
```
> `HttpTokens=required` = **IMDSv2 only**, explícito. O `aws ec2 wait` segura o terminal até o
> estado desejado — ótimo pra scripts. Dê 1–2 min pro user data e abra o `http://$IP`.

### Passo 12 — Snapshot via CLI
```bash
VOL_ID=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
  --query "Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId" --output text)

SNAP_ID=$(aws ec2 create-snapshot --volume-id $VOL_ID \
  --description "curso-snapshot-cli" --query SnapshotId --output text)

aws ec2 wait snapshot-completed --snapshot-ids $SNAP_ID && echo "snapshot pronto: $SNAP_ID"
```

---

## Parte D — Teardown com verificação (OBRIGATÓRIO) 🔥

Agora o ritual completo — **terminate**, não stop, e prova de que nada ficou:

### Passo 13 — Terminar as instâncias
```bash
# a da CLI:
aws ec2 terminate-instances --instance-ids $INSTANCE_ID
aws ec2 wait instance-terminated --instance-ids $INSTANCE_ID

# a do Console (se ainda existir): Console → Instances → curso-web →
# Instance state → Terminate instance   (ou pela CLI com o id dela)
```

### Passo 14 — Deletar snapshots e o security group da CLI
```bash
aws ec2 delete-snapshot --snapshot-id $SNAP_ID
# + o snapshot do Console: EC2 → Snapshots → selecionar → Delete snapshot

aws ec2 delete-security-group --group-id $SG_ID
# + o curso-sg-ec2 do Console (Security groups → delete) — só depois das instâncias terminadas
```

### Passo 15 — A verificação final (não pule NUNCA)
```bash
# 1. Nenhuma instância viva (terminated ainda aparece por ~1h, tudo bem):
aws ec2 describe-instances \
  --query "Reservations[].Instances[].{Id:InstanceId,Estado:State.Name,Nome:Tags[?Key=='Name']|[0].Value}" \
  --output table

# 2. Nenhum volume EBS órfão (DeleteOnTermination cuidou do raiz, mas CONFIRME):
aws ec2 describe-volumes --query "Volumes[].{Id:VolumeId,Estado:State,GB:Size}" --output table

# 3. Nenhum snapshot seu sobrando:
aws ec2 describe-snapshots --owner-ids self --query "Snapshots[].SnapshotId" --output table

# 4. Nenhum Elastic IP alocado:
aws ec2 describe-addresses
```
- ✅ Instâncias: só `terminated` (ou nada).
- ✅ Volumes: **lista vazia**.
- ✅ Snapshots: **lista vazia**.
- ✅ Addresses: **lista vazia**.
- ✅ Bônus: amanhã, olhe **Billing → Bills** e confirme ~US$ 0.

> A key pair `curso-key` pode ficar (registro de chave pública não custa nada e serve pros
> próximos módulos). O arquivo `.pem` fica guardado em `~/.ssh/`.

---

## ✅ Checklist de conclusão do módulo

- [ ] Key pair criada, `.pem` em `~/.ssh/` com `chmod 400` (e fora do repo).
- [ ] `t3.micro` lançada com AMI Amazon Linux 2023, SG (22 só seu IP, 80 aberto) e user data.
- [ ] Página do nginx acessada pelo IP público — bootstrap 100% automático.
- [ ] SSH feito; leu o `/var/log/cloud-init-output.log`.
- [ ] IMDSv2 testado: viu o **401 sem token** e as consultas com token.
- [ ] Snapshot criado e status Completed.
- [ ] Ciclo de vida sentido: stop (IP sumiu, EBS ficou), start (IP novo).
- [ ] Tudo repetido via CLI (SSM p/ AMI, run-instances, wait, create-snapshot).
- [ ] **Teardown:** instâncias terminadas, snapshots e SGs deletados, e a **verificação final**
      com as 4 listas limpas.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-04/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-04/`) e para o **Módulo 05 — Escalabilidade & Balanceamento**, onde essa
instância única vira uma frota com Auto Scaling + Load Balancer.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 4" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
