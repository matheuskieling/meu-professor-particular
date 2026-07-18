# Módulo 09 — Containers (Prática Guiada)

> Objetivo desta prática: percorrer o ciclo completo de containers na AWS — **build** local de
> uma imagem, **push** pro **ECR**, rodar no **ECS Fargate** primeiro como **task avulsa** e
> depois como **service com 2 tasks**, testar de verdade e **destruir tudo**.
>
> **Abordagem:** Console primeiro (pra ver), CLI onde ela brilha (build/push). Cada passo explica o *porquê*.
>
> ⏱️ Tempo estimado: 60–90 min.
> 💵 Custo: **não é 100% Free Tier!** Fargate cobra por task rodando: nossa config (0,25 vCPU +
> 0,5 GB) custa ~**US$ 0,012/hora por task** (~1 centavo). Fazendo a prática em até 2 h e o
> teardown no fim, o total fica em **poucos centavos de dólar**. ECR: centavos de armazenamento.
> **Não deixe tasks rodando após a prática.**

---

## ⚠️ Antes de começar — leia isto

- **Pré-requisito: Docker instalado localmente.** Verifique:

```bash
docker --version
```

  Se não tiver, instale pelo site oficial (<https://docs.docker.com/get-docker/>) ou, no Arch:
  `sudo pacman -S docker` + iniciar o serviço. Confirme com `docker run hello-world`.
- Pré-requisitos do curso: Módulo 01 (CLI), Módulo 03 (VPC default e security groups), Módulo 05 (ALB — só conceito aqui).
- Região: **us-east-1**. E lembre: **task rodando = relógio de cobrança girando**.
- **Não usaremos ALB nesta prática** (custa ~US$ 16/mês parado) — testaremos pelo IP público das tasks.

---

## Parte A — Build local da imagem

### Passo 1 — Criar a aplicação de teste
Crie uma pasta fora do repositório (ex.: `/tmp/m09-app`) com dois arquivos:

```bash
mkdir -p /tmp/m09-app && cd /tmp/m09-app
```

`server.py`:
```python
import http.server
import os
import socket

PORTA = 8080

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        corpo = f"Olá do container! host={socket.gethostname()} versao={os.environ.get('VERSAO', 'v1')}\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(corpo.encode())

http.server.HTTPServer(("", PORTA), Handler).serve_forever()
```

`Dockerfile`:
```dockerfile
FROM python:3.13-alpine
WORKDIR /app
COPY server.py .
EXPOSE 8080
CMD ["python", "server.py"]
```

> **Por quê o `hostname` na resposta:** cada task terá um hostname diferente — é assim que você
> vai *ver* as 2 tasks do service respondendo.

### Passo 2 — Build e teste local
```bash
docker build -t m09-app:v1 .
docker run --rm -p 8080:8080 m09-app:v1
```
Em outro terminal:
```bash
curl http://localhost:8080
```
Funcionou? `Ctrl+C` no `docker run`. Você tem uma **imagem** pronta pra viajar.

---

## Parte B — Publicar no ECR

### Passo 3 — Criar o repositório
Console → **ECR** → **Private registry → Repositories** → **Create repository** → nome:
`curso/m09-app` → **Create**. (Ou pela CLI: `aws ecr create-repository --repository-name curso/m09-app`.)

### Passo 4 — Login, tag e push
Pegue seu ID de conta e autentique o Docker no ECR (token de 12 h):

```bash
CONTA=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password | docker login --username AWS --password-stdin $CONTA.dkr.ecr.us-east-1.amazonaws.com
```

Agora dê à imagem o "endereço completo" e envie:

```bash
docker tag m09-app:v1 $CONTA.dkr.ecr.us-east-1.amazonaws.com/curso/m09-app:v1
docker push $CONTA.dkr.ecr.us-east-1.amazonaws.com/curso/m09-app:v1
```

Confira no Console (ECR → repositório) que a tag `v1` chegou.

> 🎯 Se der `no basic auth credentials`: o login do passo anterior faltou ou expirou. Refaça.

---

## Parte C — ECS Fargate: cluster, task definition e task avulsa

### Passo 5 — Criar o cluster
1. Console → **ECS** → **Clusters** → **Create cluster**.
2. Nome: `m09-cluster` · Infrastructure: **AWS Fargate (serverless)** → **Create**.

> Com Fargate, o cluster é só um agrupamento lógico — nenhuma máquina foi criada (nem cobrada).

### Passo 6 — Registrar a task definition
1. ECS → **Task definitions** → **Create new task definition**.
2. Family: `m09-task` · Launch type: **Fargate** · CPU: **0.25 vCPU** · Memory: **0.5 GB**.
3. Task execution role: **Create new role** (é ela que puxa a imagem do ECR e manda logs).
4. Container: nome `m09-app`, **Image URI**: `SEU_ID.dkr.ecr.us-east-1.amazonaws.com/curso/m09-app:v1`,
   **Container port: 8080**.
5. Deixe o log driver **awslogs** habilitado (cria o grupo `/ecs/m09-task`) → **Create**.

> Você criou a **receita** (revisão `m09-task:1`). Nada roda — e nada cobra — ainda.

### Passo 7 — Rodar uma task avulsa (standalone) — 💰 o relógio começa aqui
1. Cluster `m09-cluster` → aba **Tasks** → **Run new task**.
2. Launch type **Fargate** · Task definition: `m09-task` (revisão 1) · Quantidade: **1**.
3. **Networking:** VPC default, subnets públicas, **Public IP: ENABLED**.
4. Security group: crie/use um permitindo **TCP 8080** do seu IP (ou 0.0.0.0/0 pra teste rápido).
5. **Create** e aguarde o status **Running**.

### Passo 8 — Testar a task
1. Clique na task → em **Networking**, copie o **Public IP**.
2. No terminal:

```bash
curl http://IP_PUBLICO:8080
```

Resposta do seu container rodando na nuvem, sem nenhum servidor seu. 🎉 Veja também os logs:

```bash
aws logs tail /ecs/m09-task --since 10m
```

3. **Pare a task** (Stop) — task avulsa parada = cobrança encerrada. O service vem agora.

---

## Parte D — Service com 2 tasks

### Passo 9 — Criar o service
1. Cluster `m09-cluster` → aba **Services** → **Create**.
2. Launch type **Fargate** · Task definition `m09-task` · Service name: `m09-service` ·
   **Desired tasks: 2**.
3. Networking: mesma config do passo 7 (subnets públicas, public IP, SG da porta 8080).
4. Sem load balancer (economia de estudo; em produção entraria o ALB aqui) → **Create**.

### Passo 10 — Ver o service em ação
1. Aguarde as **2 tasks** ficarem Running. Pegue o IP público de cada uma e faça `curl` nos dois —
   repare nos **hostnames diferentes**: são containers distintos da mesma imagem.
2. **Teste o "gerente":** selecione uma task e **Stop**. Espere ~1 min e olhe de novo: o service
   **subiu uma substituta** sozinho, mantendo desired count = 2. É isso que um service faz.

> 💡 Em produção: ALB na frente registrando os IPs das tasks num target group (modo `awsvpc` =
> um IP por task), health checks tirando tasks doentes do rodízio e rolling update sem downtime.

---

## Parte E — 🔥 Teardown (obrigatório — aqui é a cobrança de verdade)

Ordem: **service → cluster → task definition → ECR → logs**. Via CLI:

```bash
# 1. Zerar e apagar o service (força a parada das tasks)
aws ecs update-service --cluster m09-cluster --service m09-service --desired-count 0
aws ecs delete-service --cluster m09-cluster --service m09-service --force

# 2. Conferir que NENHUMA task sobrou (deve retornar lista vazia)
aws ecs list-tasks --cluster m09-cluster

# 3. Apagar o cluster
aws ecs delete-cluster --cluster m09-cluster

# 4. Desregistrar a task definition (revisão 1)
aws ecs deregister-task-definition --task-definition m09-task:1

# 5. Apagar o repositório ECR com as imagens
aws ecr delete-repository --repository-name curso/m09-app --force

# 6. Apagar o log group
aws logs delete-log-group --log-group-name /ecs/m09-task
```

> ⚠️ **Checagem dupla anti-custo:** no Console, ECS → Clusters deve estar vazio e **nenhuma task
> Running em nenhum cluster**. Task esquecida rodando = cobrança contínua (pequena, mas real).
> Se criou um security group só pra isso, pode removê-lo também (não custa, mas é higiene).

Local (opcional): `docker rmi` das imagens e `rm -rf /tmp/m09-app`.

---

## ✅ Checklist de conclusão do módulo

- [ ] `docker --version` ok e imagem `m09-app:v1` buildada e testada localmente.
- [ ] Repositório `curso/m09-app` criado no ECR.
- [ ] Login no ECR + `docker push` da imagem com sucesso.
- [ ] Cluster Fargate `m09-cluster` criado.
- [ ] Task definition `m09-task` registrada (0.25 vCPU / 0.5 GB, porta 8080, awslogs).
- [ ] Task avulsa rodou e respondeu ao `curl` pelo IP público.
- [ ] Service `m09-service` manteve 2 tasks e **repôs** a task que você parou.
- [ ] **Teardown completo** — zero tasks rodando, cluster/repo/logs apagados.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-09/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-09/`) e para o **Módulo 10 — Mensageria & Integração**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 9" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
