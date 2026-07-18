# Curso 1 — AWS & Cloud (Mega Intensivo)

Curso intensivo de **AWS e computação em nuvem**, do zero ao avançado. O objetivo final é dar
a um desenvolvedor **plena autonomia para gerenciar ambientes cloud**: provisionar, proteger,
escalar, monitorar e otimizar custos de infraestrutura na AWS com confiança.

## Público-alvo

Desenvolvedor que já programa, mas quer dominar cloud/AWS de forma sólida — não apenas "clicar
no console", e sim entender os fundamentos, as decisões de arquitetura e as boas práticas.

## Objetivos de aprendizado

Ao final, o aluno deve ser capaz de:
- Entender os fundamentos de cloud (modelos de serviço, regiões, AZs, responsabilidade compartilhada).
- Operar a AWS com segurança (IAM, contas, billing, least privilege).
- Provisionar e gerenciar compute, rede, storage e banco de dados.
- Desenhar arquiteturas resilientes, escaláveis e econômicas.
- Automatizar infraestrutura (IaC) e adotar boas práticas de DevOps/CI-CD.
- Monitorar, observar e responder a incidentes.
- Gerenciar e otimizar custos (FinOps).
- Estar preparado para certificações oficiais (a começar pelo Cloud Practitioner).

---

## O formato do curso: aula ao vivo (one-on-one)

O curso foi pensado para ser um **one-on-one com o Claude**, não uma leitura solitária. O Claude
**conduz** a aula: explica um ponto por vez, com as próprias palavras, convida dúvidas e pergunta
**"posso continuar?"** antes de avançar. Ao fim da teoria, propõe passar à prática; guia a prática;
depois conduz quiz e prova. **O estado (onde paramos) é salvo**, então dá pra parar e retomar sempre.

Isso é operado pelo driver **`apps/aula.py`**, que lê o **`roteiro.json`** do módulo (a lista
ordenada de "beats" a ensinar) e persiste o progresso. Guia de uso completo em `apps/CLAUDE.md`.
Os arquivos `.md` (teoria/prática) continuam existindo para quem quiser **estudar sozinho** — ver `README.md`.

**Como o Claude conduz uma aula:**
1. `python3 AWS/apps/aula.py current` (ou `start ...` na primeira vez) para ver o beat atual.
2. Lê os `pontos` e **narra com as próprias palavras** — nunca cola os bullets crus.
3. No `checkpoint`, pausa: convida dúvidas e pergunta se pode seguir.
4. Ao "pode seguir", `aula.py next`. Se surgir dúvida relevante, `aula.py note "..."`.
5. Em beats de fase `quiz`/`prova`, dispara o `session.py` correspondente (ver abaixo).
6. Para retomar noutro dia: `aula.py current` volta exatamente ao ponto salvo.

## Como cada módulo funciona (anatomia de um módulo)

Todo módulo segue **a mesma estrutura**, pensada para o ciclo *aprender → praticar → testar → avaliar*.
Ao criar um módulo novo, replique exatamente este formato:

### 0. Roteiro da aula — `NN-nome/roteiro.json`
A espinha da **aula ao vivo**: os "beats" ordenados (teoria → prática → quiz → prova → fechamento),
cada um com pontos-chave, checkpoint e referência às seções de `teoria.md`/`pratica.md`. É o que o
Claude segue ao conduzir. Formato no cabeçalho de `apps/aula.py`.

### 1. Teoria — `NN-nome/teoria.md`
Texto teórico explicando **o quê**, **o porquê** e o contexto. Linguagem direta, com analogias,
tabelas, armadilhas comuns e um glossário. Fecha com uma seção de **checagem de entendimento**.

### 2. Prática guiada — `NN-nome/pratica.md`
Execução real na AWS, passo a passo. **Abordagem: os dois** — primeiro o **Console web** (pra
*ver* o que acontece), depois a **AWS CLI** (pra *fixar, reproduzir e automatizar*). Sempre inclui:
- avisos de **custo** (o que é Free Tier, o que cobra);
- checklist de conclusão;
- 🔥 **teardown** obrigatório (destruir recursos pagos ao final).

### 3. Aplicação de teste da aula — `apps/modulo-NN/`
Um **quiz** que reforça a aula, com banco de questões em `questions.json`. Roda em **dois modos**:

- **Modo conduzido pelo Claude (preferido):** o Claude opera a app como uma sessão persistente e
  faz as perguntas **aqui no chat**. O aluno responde em linguagem natural, **tira dúvidas a
  qualquer momento**, pede dicas ou para aprofundar; o Claude repassa a resposta à sessão e explica
  o resultado. É uma *máquina de estado* (sem stdin travado), então é robusto:
  ```bash
  python3 AWS/apps/session.py start AWS/apps/modulo-NN/questions.json   # mostra a Q1
  python3 AWS/apps/session.py answer B                                  # corrige e avança
  python3 AWS/apps/session.py status                                    # progresso/nota
  ```
  Use `--id <nome>` para sessões paralelas (ex.: `--id prova`, `--id cert`). O mesmo `session.py`
  roda **qualquer** banco (aula, prova ou certificação).

- **Modo solo:** o aluno roda sozinho e responde pelo teclado:
  ```bash
  python3 AWS/apps/modulo-NN/quiz.py
  ```

### 4. Prova do módulo — `provas/modulo-NN/`
Avaliação de fim de módulo, mais abrangente. **Diferencial:** feedback **por alternativa** — com
base na opção escolhida, explica por que sua resposta está certa/errada e, se errou, qual é a
correta e por quê (campo `feedbacks` no `questions.json`). Aprovação: **70%**. Conduzida pelo Claude
via `session.py ... --id prova`, ou solo via `provas/modulo-NN/prova.py`.

### 5. Preparação para certificação — `certificacoes/`
Simulados no formato do **exame oficial** (misturam assuntos, estilo "qual a MELHOR opção"). Vivem
separados por certificação (ex.: `clf-c02/`) e **crescem** conforme o curso avança. Mesmo driver:
`session.py ... --id cert`.

> **Resumo do fluxo de uma aula:** ler `teoria.md` → fazer a `pratica.md` na AWS → rodar o **quiz**
> (Claude conduz e tira dúvidas) → ao fim do módulo, a **prova** → periodicamente, **simulados de
> certificação**. As apps são Python puro, **sem dependências** (`python3` e pronto). Detalhes do
> formato de `questions.json` em `apps/CLAUDE.md`.

---

## Metodologia (resumo)

Ciclo **teoria → prática guiada → teste → avaliação**:
1. **Teoria** — entender o porquê.
2. **Prática guiada** — Console primeiro, depois CLI; execução real explicada passo a passo.
3. **Teste (quiz)** — Claude conduz no chat, tirando dúvidas.
4. **Avaliação (prova + simulados)** — feedback por alternativa; preparo para certificação.

> ⚠️ **Custos e segurança:** a AWS cobra por recursos reais. Toda prática deixa claro o que gera
> custo, prioriza o **Free Tier** e sempre inclui **teardown**. Nunca versionar credenciais, chaves
> de acesso ou secrets (o `.gitignore` já bloqueia; as chaves ficam só em `~/.aws/`).

---

## Plano completo do curso

Currículo planejado de ponta a ponta, organizado em fases. A ordem pode ser ajustada, mas o destino
é dar autonomia plena. **Legenda de status:** ✅ pronto · 🔜 próximo · ⬜ planejado.

### Fase 1 — Fundamentos
| # | Módulo | Objetivo | Status |
|---|--------|----------|--------|
| 01 | Fundamentos de Cloud & AWS | Nuvem, modelos de serviço, regiões/AZs, responsabilidade compartilhada, custos, CLI. | ✅ |
| 02 | Conta, IAM & Segurança | Root vs. IAM, users/groups/roles/policies, MFA, least privilege, billing/alertas. | 🔜 |

### Fase 2 — Infraestrutura core
| # | Módulo | Objetivo | Status |
|---|--------|----------|--------|
| 03 | Rede — VPC | VPC, subnets, route tables, IGW/NAT, security groups, NACLs, VPC peering. | ⬜ |
| 04 | Compute — EC2 | Instâncias, AMIs, tipos, key pairs, user data, EBS, snapshots. | ⬜ |
| 05 | Escalabilidade & Balanceamento | Auto Scaling Groups, Launch Templates, ELB (ALB/NLB), health checks. | ⬜ |
| 06 | Storage — S3 & cia | S3 (buckets, políticas, versionamento, lifecycle, criptografia), EBS, EFS, Glacier. | ⬜ |

### Fase 3 — Dados & aplicações
| # | Módulo | Objetivo | Status |
|---|--------|----------|--------|
| 07 | Bancos de dados | RDS (Multi-AZ, réplicas, backups), Aurora, DynamoDB, ElastiCache. | ⬜ |
| 08 | Serverless | Lambda, API Gateway, event-driven, noções de Step Functions. | ⬜ |
| 09 | Containers | Docker na AWS, ECR, ECS (Fargate), visão geral de EKS. | ⬜ |
| 10 | Mensageria & Integração | SQS, SNS, EventBridge; padrões de desacoplamento. | ⬜ |

### Fase 4 — Operação & automação
| # | Módulo | Objetivo | Status |
|---|--------|----------|--------|
| 11 | Infra como Código (IaC) | CloudFormation e/ou Terraform; ambientes reproduzíveis e versionados. | ⬜ |
| 12 | Observabilidade | CloudWatch (métricas/logs/alarmes/dashboards), CloudTrail, X-Ray. | ⬜ |
| 13 | Segurança avançada | KMS, Secrets Manager, WAF, Shield, GuardDuty, IAM avançado. | ⬜ |
| 14 | DNS & Entrega de conteúdo | Route 53 (roteamento), CloudFront (CDN), certificados (ACM). | ⬜ |

### Fase 5 — Arquitetura & avançado
| # | Módulo | Objetivo | Status |
|---|--------|----------|--------|
| 15 | Arquitetura & Well-Architected | Os 6 pilares; padrões resilientes, escaláveis e econômicos. | ⬜ |
| 16 | CI/CD & DevOps | CodePipeline/CodeBuild/CodeDeploy (ou GitHub Actions), deploy automatizado. | ⬜ |
| 17 | Otimização de Custos (FinOps) | Right-sizing, Savings Plans/RIs, Spot, tags, Cost Explorer, budgets. | ⬜ |
| 18 | Alta Disponibilidade & DR | Estratégias multi-AZ/multi-região, RTO/RPO, backup e recuperação. | ⬜ |

### Fase 6 — Consolidação
| # | Módulo | Objetivo | Status |
|---|--------|----------|--------|
| 19 | Projeto final (capstone) | Projetar e subir uma arquitetura completa do zero, aplicando tudo. | ⬜ |

### Trilha de certificações (paralela ao curso)
- **CLF-C02** — Cloud Practitioner (após Fase 1–2). Simulado já iniciado em `certificacoes/clf-c02/`.
- **SAA-C03** — Solutions Architect Associate (após Fase 4–5).
- **SOA-C02 / DVA-C02** — SysOps / Developer Associate (conforme interesse).

---

## Estrutura de arquivos

```
AWS/
├── README.md                 ← como fazer o curso (para o aluno)
├── CLAUDE.md                 ← este arquivo
├── 01-fundamentos/
│   ├── roteiro.json          ← roteiro da aula ao vivo (o Claude conduz)
│   ├── teoria.md
│   └── pratica.md
├── 02-iam-seguranca/         (próximo)
│   └── ...
├── apps/                     ← drivers (aula/quiz) + quizzes das aulas
│   ├── CLAUDE.md
│   ├── aula.py               ← driver de aula ao vivo (roteiro + progresso)
│   ├── session.py            ← driver de quiz/prova conduzido pelo Claude
│   ├── quiz_engine.py        ← motor do quiz no modo solo
│   ├── reset.py              ← zera o progresso local (recomeçar do início)
│   └── modulo-01/
│       ├── quiz.py
│       └── questions.json
├── provas/                   ← provas de fim de módulo (feedback por alternativa)
│   ├── CLAUDE.md
│   └── modulo-01/
│       ├── prova.py
│       └── questions.json
└── certificacoes/            ← simulados no formato dos exames oficiais
    ├── CLAUDE.md
    └── clf-c02/
        └── questions.json
```

---

## Estado atual

- ✅ **Módulo 01 — Fundamentos** completo: roteiro (aula ao vivo), teoria, prática, quiz, prova e
  simulado CLF-C02 inicial. README do curso escrito.
- 🔜 **Próximo:** conduzir a aula ao vivo do M01 com o aluno (`apps/aula.py`) ou iniciar o
  **Módulo 02 — Conta, IAM & Segurança**.
