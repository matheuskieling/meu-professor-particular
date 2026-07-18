# Roadmap — futuro do curso de AWS

> **Status deste documento:** é um **plano** do que faremos no futuro. Nada aqui está implementado
> ainda além do "tronco comum". Ele registra as **trilhas de especialização** (caminhos separados),
> os **módulos e simulados** que cada certificação vai exigir, e o **mecanismo de navegação** que o
> curso ganhará para o aluno escolher, retomar e concluir cada trilha.

## Onde estamos hoje — o "tronco comum"

Os **módulos 01–19** já prontos formam o tronco comum do curso e preparam para:
- ✅ **CLF-C02** — Cloud Practitioner (simulados prontos)
- ✅ **SAA-C03** — Solutions Architect Associate (simulados prontos)

Depois de concluir o tronco e essas duas certificações "básicas", o curso **se ramifica**.

## A visão: tronco comum → trilhas separadas

```
                          ┌─→ Trilha Developer (DVA-C02)
                          ├─→ Trilha SysOps (SOA-C02)
   Tronco comum           ├─→ Trilha Data Engineer (DEA-C01)
   (mód. 01–19            ├─→ Trilha ML Engineer (MLA-C01)
    + CLF-C02 + SAA-C03) ─┼─→ Trilha AI Practitioner (AIF-C01)
                          ├─→ Trilha Security (SCS-C02)
                          ├─→ Trilha Advanced Networking (ANS-C01)
                          ├─→ Trilha SA Professional (SAP-C02)
                          └─→ Trilha DevOps Professional (DOP-C02)
```

Cada trilha é um **caminho independente**: tem seus próprios módulos novos + banco rápido + 3 provas
completas da certificação (mesmo padrão do que já fizemos). O aluno escolhe as trilhas por interesse,
na ordem que quiser (respeitando pré-requisitos), e pode fazer só uma, algumas ou todas.

## Estrutura de arquivos planejada

```
AWS/
├── 01-fundamentos/ ... 19-projeto-final/   ← tronco comum (FEITO)
├── trilhas/                                ← A CRIAR
│   ├── developer-dva/NN-nome/{roteiro.json,teoria.md,pratica.md}
│   ├── sysops-soa/...
│   ├── data-engineer-dea/...
│   ├── ml-engineer-mla/...
│   ├── ai-practitioner-aif/...
│   ├── security-scs/...
│   ├── networking-ans/...
│   ├── sa-professional-sap/...
│   └── devops-professional-dop/...
├── apps/                                   ← drivers (reusar; estender p/ trilhas — ver abaixo)
└── certificacoes/
    ├── clf-c02/, saa-c03/                  ← FEITO
    └── dva-c02/, soa-c02/, dea-c01/, mla-c01/, aif-c01/, scs-c02/, ans-c01/, sap-c02/, dop-c02/
                                            ← A CRIAR (banco rápido + prova-1/2/3, 65q cada)
```

## As trilhas e o que cada uma exige

### Prioridade 1 — Associate (reaproveitam muito do tronco)

**Trilha Developer — DVA-C02** (Associate)
- Pré-requisito: tronco comum.
- Módulos novos: SDK & `boto3` aprofundado; autenticação (Cognito user/identity pools, JWT, OAuth);
  DynamoDB avançado (single-table design, streams, DAX, transações); deploy serverless (SAM/CDK,
  Lambda layers, versions/aliases, config); CI/CD para devs (CodeCommit/Build/Deploy/Pipeline,
  CodeArtifact, X-Ray); mensageria aplicada (SQS/SNS/EventBridge em apps); caching (ElastiCache,
  API Gateway); segurança no código (KMS, Secrets Manager, Parameter Store em runtime).

**Trilha SysOps — SOA-C02** (Associate)
- Pré-requisito: tronco comum.
- Módulos novos: Systems Manager profundo (Run Command, State/Patch Manager, Session Manager,
  Automation); monitoramento avançado (CloudWatch agent, métricas custom, dashboards, alarmes
  compostos, Logs Insights); automação de resposta (EventBridge + SSM/Lambda); backup & DR
  operacional (AWS Backup, automação de snapshots); estratégias de deploy (blue/green, rolling com
  ELB/ASG); operação multi-conta (Organizations, Control Tower); troubleshooting (rede, permissões,
  capacidade); custos operacionais (anomaly detection, right-sizing, budget actions).

### Prioridade 2 — Associate de dados/IA (exigem conteúdo novo)

**Trilha Data Engineer — DEA-C01** (Associate)
- Módulos novos: ingestão (Kinesis Data Streams/Firehose, DMS, DataSync); data lake (S3, Lake
  Formation, Parquet/ORC, particionamento); processamento (Glue ETL, EMR/Spark, DataBrew); query
  (Athena, Redshift + Spectrum); orquestração (Step Functions, MWAA/Airflow, Glue workflows);
  streaming analytics (Managed Flink); governança e qualidade de dados; otimização de custo/formato.

**Trilha ML Engineer — MLA-C01** (Associate)
- Módulos novos: fundamentos de ML aplicados; preparação de dados (SageMaker Data Wrangler, Feature
  Store); treinamento e tuning (SageMaker Training, HPO); deploy (endpoints, batch transform,
  multi-model); MLOps (SageMaker Pipelines, Model Registry, monitoramento de drift); serviços de IA
  gerenciados; segurança e custo de ML.

### Prioridade 3 — Foundational de IA

**Trilha AI Practitioner — AIF-C01** (Foundational)
- Pré-requisito: nenhum além do tronco (pode ser feita cedo).
- Módulos novos: conceitos de IA/ML/IA generativa; Amazon Bedrock (modelos, prompts, RAG, agents);
  serviços de IA (Rekognition, Comprehend, Textract, Transcribe, Polly, Translate); visão geral do
  SageMaker; IA responsável (viés, transparência, segurança); casos de uso e custo.

### Prioridade 4 — Specialty

**Trilha Security — SCS-C02**
- Módulos novos: IAM avançado (policies complexas, ABAC, permission boundaries, cross-account);
  detecção (GuardDuty, Security Hub, Detective, Inspector, Macie, Config rules); proteção de infra
  (WAF, Shield, Network Firewall); criptografia profunda (KMS, CloudHSM, envelope, rotação, key
  policies); identidade (Identity Center, federação, IAM Roles Anywhere); resposta a incidentes;
  logging/auditoria (CloudTrail, VPC Flow Logs).

**Trilha Advanced Networking — ANS-C01**
- Módulos novos: VPC avançado (IPv6, CIDRs secundários); conectividade híbrida (Direct Connect,
  Site-to-Site VPN, DX Gateway); escala (Transit Gateway, PrivateLink, peering em escala); DNS
  avançado (Route 53 Resolver, DNS híbrido, policies); entrega global (CloudFront avançado, Global
  Accelerator); segurança de rede (Network Firewall, NACL em escala); observabilidade de rede
  (Flow Logs, Reachability Analyzer); otimização de custo de rede.

> *Machine Learning Specialty (MLS-C01) fica como opcional/legado — a AWS vem direcionando esse
> público para a trilha MLA-C01 + AIF-C01.*

### Prioridade 5 — Professional (topo da trilha)

**Trilha SA Professional — SAP-C02**
- Pré-requisito recomendado: SAA-C03 + trilhas relevantes.
- Módulos novos: multi-account em escala (Organizations, Control Tower, Landing Zone); migração
  complexa (7 Rs, portfólio, MGN/DMS em escala); redes híbridas avançadas; continuidade (DR
  multi-region, RTO/RPO agressivos); segurança e governança em escala; otimização de custo em
  escala; modernização (containers/serverless/event-driven em larga escala).

**Trilha DevOps Professional — DOP-C02**
- Pré-requisito recomendado: SOA-C02 e/ou DVA-C02.
- Módulos novos: CI/CD avançado (pipelines multi-stage/multi-account, aprovações); IaC em escala
  (CloudFormation StackSets, CDK, Terraform); configuração e automação (SSM em escala); observabilidade
  (métricas/logs/traces, SLOs); resiliência e auto-recuperação; governança automatizada (Config,
  guardrails); incident response e chaos engineering.

## Mecanismo de navegação por trilhas (a implementar)

Hoje o `engine/aula.py` conduz um roteiro linear. Para as trilhas, o curso precisará de:

1. **Registro de trilhas** — um índice (ex.: `AWS/trilhas/trilhas.json`) listando cada trilha:
   código da cert, título, pré-requisitos, ordem dos módulos, e status (`bloqueada`/`disponível`/
   `em andamento`/`concluída`).
2. **Menu de escolha ao concluir o tronco** — quando o aluno termina os módulos 01–19 (e passa em
   CLF/SAA), o `/retomar-curso` deixa de seguir linearmente e **apresenta as trilhas disponíveis**,
   pedindo qual seguir (o aluno pode navegar/explorar as ramificações com ajuda do agente).
3. **Persistência da escolha** — a trilha escolhida (e o progresso dentro dela) é **salva no estado**
   (`.sessions/`, versionado no fork/branch do aluno). Ao retomar, o curso **parte da trilha
   corrente** automaticamente.
4. **Marcar como concluída** — ao terminar uma trilha (módulos + simulados no portão de prontidão),
   o curso **marca a trilha como feita** no estado e **oferece a próxima** disponível.
5. **Trocar de trilha** — o aluno pode pausar uma trilha e começar/retomar outra a qualquer momento;
   o estado guarda o progresso de cada uma separadamente.

Arquivos que serão tocados quando formos implementar: `engine/aula.py` (suporte a trilhas + estado de
múltiplas trilhas), `.claude/skills/retomar-curso/SKILL.md` (passo de escolha/retomada de trilha) e
os ponteiros dos outros harnesses (só referenciam o SKILL.md, então seguem válidos).

## Ordem sugerida de construção

1. **DVA-C02** e **SOA-C02** (reaproveitam ~70–80% do tronco — menor esforço, alto valor).
2. **AIF-C01** (foundational, conteúdo novo mas enxuto e em alta).
3. **DEA-C01** / **MLA-C01** (dados e IA, conteúdo novo).
4. **SCS-C02** / **ANS-C01** (specialty).
5. **SAP-C02** / **DOP-C02** (professional, exigem os anteriores como base).

Cada item acima, quando for a hora, replica o padrão já validado: módulos (roteiro + teoria +
prática + quiz + prova) e a pasta de certificação com banco rápido + 3 provas de 65 questões.

## Quer seguir antes da gente construir? (faça no seu fork)

Este roadmap é escrito para ser **acionável por qualquer agente**. Se uma trilha ainda não foi
construída e você quer avançar nela agora, **não precisa esperar** — é só pedir ao seu harness, no
**seu próprio fork/branch**, algo como:

> "Seguindo o `AWS/ROADMAP.md`, construa a trilha **DVA-C02**: crie os módulos em
> `AWS/trilhas/developer-dva/` (roteiro + teoria + prática + quiz + prova, no mesmo formato do
> tronco) e a pasta `AWS/certificacoes/dva-c02/` com banco rápido + 3 provas de 65 questões. Depois
> me conduza por ela."

O agente tem tudo o que precisa: este roadmap diz **o que** cada trilha exige, e o `CLAUDE.md` do
curso + `engine/CLAUDE.md` dizem **como** um módulo/prova é montado (formato dos arquivos, drivers,
padrão das questões). Como o conteúdo mora no **seu fork**, você pode construir e estudar sua trilha
sem depender do repositório principal — e, se quiser, depois abrir um PR para contribuir de volta.

> Enquanto o **mecanismo de navegação por trilhas** (menu automático ao fim do tronco, escolha
> salva no estado, marcação de concluída) não existir, a condução é manual: peça ao agente para
> conduzir a trilha recém-criada com `engine/aula.py` apontando para os novos `roteiro.json`, do mesmo
> jeito que o tronco. Funciona igual — só não é automático ainda.
