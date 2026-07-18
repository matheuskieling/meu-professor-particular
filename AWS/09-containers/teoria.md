# Módulo 09 — Containers (Teoria)

> Objetivo do módulo: revisar rapidinho o essencial de **Docker**, entender onde as imagens moram
> na AWS (**ECR**) e como rodá-las de forma gerenciada com **ECS** — focando no launch type
> **Fargate** (serverless de containers). No fim, você vai saber escolher entre **ECS, EKS e App
> Runner** e terá uma visão conceitual de **EKS/Kubernetes**. Este módulo é o meio do caminho entre
> o EC2 (Módulo 04, você gerencia tudo) e o Lambda (Módulo 08, você não gerencia nada).

---

## 1. Recap rápido de Docker (o mínimo que você precisa)

Container **não é** uma VM. Uma VM virtualiza hardware e carrega um SO inteiro; um container é um
**processo isolado** que compartilha o kernel do host, mas enxerga seu próprio filesystem, rede e
recursos. Resultado: sobe em milissegundos e pesa megabytes, não gigabytes.

Os quatro conceitos que sustentam tudo:

| Conceito | O que é |
|----------|---------|
| **Imagem** | O "pacote congelado": filesystem + app + dependências + config. Imutável, versionada por **tags** (`minha-app:1.2`). |
| **Container** | Uma **instância em execução** de uma imagem. Efêmero: morreu, perdeu o que não foi salvo fora. |
| **Dockerfile** | A "receita" pra construir a imagem: `FROM` (base), `COPY` (código), `RUN` (instalar), `CMD` (o que executa). |
| **Registry** | O "repositório de imagens": onde você faz `push` (publicar) e `pull` (baixar). Docker Hub é o público famoso; na AWS é o **ECR**. |

O ciclo de vida que você vai executar na prática:

```
Dockerfile ──build──▶ imagem ──push──▶ registry (ECR) ──pull──▶ container rodando (ECS)
```

**Por que containers ganharam o mundo:** a imagem que rodou na sua máquina é **byte a byte a
mesma** que roda em produção. Acabou o "na minha máquina funciona" — dependências, runtime e SO
de usuário viajam juntos.

> 💡 Se Docker ainda é nebuloso pra você, pause aqui e pratique local antes de seguir — a prática
> deste módulo assume `docker build/run` básicos.

---

## 2. ECR — Elastic Container Registry

O **ECR** é o registry gerenciado da AWS: privado por padrão, integrado ao IAM, com criptografia
e scan de vulnerabilidades opcional.

- **Repositório**: um por aplicação/imagem (ex.: `curso/m09-app`). Dentro dele, as **tags** das
  versões (`latest`, `v1`, `v2`...).
- **URI da imagem**: o endereço completo que o ECS vai usar:
  `123456789012.dkr.ecr.us-east-1.amazonaws.com/curso/m09-app:latest`
  (conta + região + repositório + tag).
- **Autenticação**: o Docker não fala IAM nativamente, então você troca credenciais IAM por um
  token de login de 12 horas:

```bash
aws ecr get-login-password | docker login --username AWS --password-stdin <conta>.dkr.ecr.us-east-1.amazonaws.com
```

- **Custo**: armazenamento ~US$ 0,10/GB-mês em repositórios privados. Imagens pequenas de estudo
  = centavos; ainda assim, teardown.

> ⚠️ **Armadilha clássica:** `docker push` falhando com `no basic auth credentials` ou
> `authorization token expired` = você não fez (ou expirou) o `get-login-password`. O token dura
> 12 h — refaça o login e siga.

---

## 3. ECS — os 4 conceitos que destravam tudo

O **ECS (Elastic Container Service)** é o orquestrador de containers "da casa" da AWS: ele decide
**onde** rodar seus containers, **quantos**, reinicia os que morrem e integra com ALB, IAM e
CloudWatch. O vocabulário é a parte que mais confunde iniciantes — grave estes quatro:

| Conceito | Analogia | O que é |
|----------|----------|---------|
| **Cluster** | O "condomínio" | Agrupamento lógico onde tasks rodam. Com Fargate, é quase só um nome. |
| **Task definition** | A "receita do prato" | O blueprint versionado: qual(is) imagem(ns), CPU/memória, portas, env vars, IAM roles, logs. Cada mudança gera uma **revisão** (`m09-task:1`, `:2`...). |
| **Task** | O "prato servido" | Uma **instância em execução** de uma task definition (1+ containers). Efêmera. |
| **Service** | O "gerente do restaurante" | Mantém **N tasks rodando sempre**: uma morre, ele sobe outra; integra com load balancer e auto scaling. |

Fluxo mental: você **registra** uma task definition, e então ou **roda uma task avulsa**
(standalone — jobs, testes) ou cria um **service** ("mantenha 2 cópias no ar, sempre") — que é o
caso de aplicações de longa duração, como APIs.

### Duas roles diferentes (pegadinha de prova)

- **Task execution role** — usada pela **infraestrutura ECS** pra *preparar* a task: puxar a
  imagem do ECR e enviar logs pro CloudWatch.
- **Task role** — usada pelo **seu código** dentro do container pra falar com a AWS (ler S3,
  fila SQS...). É o equivalente à execution role do Lambda.

---

## 4. Launch types: Fargate vs. EC2

A task definition diz **o que** rodar; o **launch type** diz **em cima de quê**:

| | **Fargate** (foco do curso) | **EC2** |
|---|---|---|
| Quem provê as máquinas | AWS (invisíveis pra você) | Você (instâncias EC2 suas no cluster) |
| Patch/escala dos hosts | AWS | Você |
| Cobrança | Por **vCPU-hora + GB-hora** da task, enquanto roda | Pelas instâncias EC2 (ligadas, cheias ou vazias) |
| Controle fino (GPU, tipos de instância, daemons) | Limitado | Total |
| Quando usar | Padrão: sem gerenciar host | GPU, custo otimizado em larga escala, requisitos especiais |

**Fargate é "serverless de containers"**: você declara CPU/memória da task e a AWS materializa a
capacidade. Sem AMI, sem patch de host, sem capacity planning. Preço de referência (us-east-1):
~**US$ 0,04/vCPU-hora + US$ 0,004/GB-hora** — uma task de 0,25 vCPU + 0,5 GB custa ~**US$ 0,012/h**
(~1 centavo de dólar por hora). Barato, mas **cobra enquanto existir task rodando** — por isso o
teardown deste módulo é pra valer.

> 💡 Conectando os módulos: Lambda = função por evento (paga por invocação, máx 15 min);
> Fargate = container de longa duração (paga por hora de task, sem limite de duração). O job de
> 45 minutos que não coube no Lambda? Roda aqui.

---

## 5. ALB na frente de um service

Você já conhece o **ALB** do Módulo 05. Com ECS ele se encaixa assim: o service registra cada
task num **target group**, o ALB distribui o tráfego entre elas e o **health check** derruba do
rodízio as que não respondem — e o service repõe.

```
internet ──▶ ALB ──▶ target group ──▶ task 1 / task 2 / task N (service ECS)
```

Detalhes que importam:
- Com rede **awsvpc** (padrão no Fargate), **cada task tem sua própria ENI/IP** — o target group
  registra **IPs**, não instâncias.
- Deploy sem downtime: o service sobe tasks novas, espera ficarem saudáveis no target group, e só
  então mata as antigas (rolling update).
- ⚠️ **Custo:** ALB cobra ~US$ 0,022/hora + LCUs (~US$ 16/mês parado!). Na prática deste módulo
  vamos testar as tasks **direto pelo IP público** pra não pagar ALB — em produção, ALB sempre.

---

## 6. ECS vs. EKS vs. App Runner — qual usar?

A AWS tem três jeitos principais de rodar containers gerenciados. O critério é **quanto controle
você precisa vs. quanta complexidade aceita**:

| | **App Runner** | **ECS (Fargate)** | **EKS** |
|---|---|---|---|
| O que é | PaaS: aponta a imagem/repo, ganha URL com TLS e auto scaling | Orquestrador da AWS, integração nativa, vocabulário simples | Kubernetes gerenciado (padrão da indústria) |
| Complexidade | Mínima | Média | Alta |
| Controle | Baixo | Médio/alto | Total |
| Custo base | Paga pelo uso do app | Paga pelas tasks | **+ ~US$ 0,10/h só pelo control plane** (~US$ 73/mês) + nós |
| Quando | Web app/API simples, quer só "subir" | **Padrão na AWS** pra maioria dos times | Já usa/precisa de Kubernetes, multi-cloud, ecossistema K8s |

Regra prática: **comece pelo mais simples que atende**. App Runner pra um web app direto; ECS
Fargate como padrão versátil; EKS quando o **ecossistema Kubernetes** for requisito real (times
com experiência K8s, ferramentas do ecossistema, portabilidade entre clouds).

### EKS em 60 segundos (só o conceitual)

**Kubernetes (K8s)** é o orquestrador open source dominante. Conceitos-espelho pra você mapear:
**pod** ≈ task (menor unidade, 1+ containers), **deployment** ≈ service do ECS (mantém N réplicas),
**service K8s** ≈ o lado de rede/balanceamento, **node** = máquina que roda pods. O **EKS** entrega
o **control plane** do Kubernetes gerenciado pela AWS; os nós podem ser EC2 ou **Fargate**. Você
opera com `kubectl` e manifests YAML — a AWS cuida da saúde do control plane. Neste curso não
praticamos EKS: o objetivo é você **saber o que é e quando escolhê-lo**.

---

## 7. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| Imagem | Pacote imutável com app + dependências, versionado por tags. |
| Container | Instância em execução de uma imagem; processo isolado, efêmero. |
| Dockerfile | Receita de build da imagem (FROM, COPY, RUN, CMD). |
| Registry / ECR | Onde imagens são publicadas (push) e baixadas (pull); ECR = o da AWS, privado + IAM. |
| Cluster (ECS) | Agrupamento lógico onde as tasks rodam. |
| Task definition | Blueprint versionado: imagem, CPU/memória, portas, roles, logs. |
| Task | Execução de uma task definition (1+ containers). |
| Service | Mantém N tasks sempre rodando; repõe as que morrem; integra com ALB. |
| Fargate | Launch type serverless: AWS provê a capacidade; paga por vCPU/GB-hora da task. |
| Task execution role vs. task role | A da infra (pull ECR, logs) vs. a do seu código (falar com AWS). |
| EKS | Kubernetes gerenciado pela AWS (control plane); pods/deployments/nodes. |
| App Runner | O jeito PaaS: da imagem à URL pública sem tocar em orquestrador. |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Qual a diferença entre **imagem** e **container**? E entre **task definition** e **task**?
2. No ECS, o que o **service** faz que uma task standalone não faz?
3. **Fargate vs. EC2** como launch type: o que muda na sua responsabilidade e na cobrança?
4. Qual a diferença entre **task execution role** e **task role**?
5. Um time sem experiência em Kubernetes quer subir uma API containerizada na AWS. ECS, EKS ou
   App Runner? Justifique — e diga quando EKS passaria a fazer sentido.

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
