# Módulo 19 — Projeto Final (Capstone) — GUIA DE EXECUÇÃO

> Este é o guia de execução **por fases** do projeto descrito no briefing (`teoria.md`).
> Cada fase tem objetivo, passos sugeridos e um **marco de verificação** — só avance com o marco
> batido (o Claude verifica com você). O guia sugere; **as decisões são suas**.
>
> ⏱️ Tempo estimado: 2–5 sessões de trabalho. 💵 Custo alvo: **≤ US$ 5 no total** — este é o
> único módulo com recursos ligados por dias. Leia os avisos de custo de cada fase.

---

## ⚠️ Antes de tudo — as regras de custo do projeto

1. Crie **já** um budget `capstone` de **US$ 5** com alertas em 50/80/100% (Módulo 17).
2. **Tudo** recebe a tag `Projeto=capstone` (ative-a como cost allocation tag).
3. Custos de referência por dia (região `us-east-1`, aproximados): ALB ~US$ 0,60 · NAT Gateway
   ~US$ 1,10 + GB · `t3.micro` ~US$ 0,25 · RDS `db.t3.micro` Multi-AZ ~US$ 0,80 ·
   DynamoDB/Lambda em baixa escala ~centavos. **Faça as contas do SEU design.**
4. Entre sessões de trabalho: desligue/reduza o que puder (ASG a 0, parar RDS) — ou, se seu IaC
   está redondo, `destroy` e `apply` de novo amanhã (é o superpoder do Módulo 11 😉).
5. **NAT Gateway é opcional.** Questione se você precisa dele (instâncias em subnet pública com
   SG restritivo, ou VPC endpoints, ou serverless dispensam). Decisão de arquitetura = decisão de custo.

---

## Fase 1 — Design & estimativa (custo: US$ 0)

**Objetivo:** decidir e documentar a arquitetura **antes** de criar qualquer recurso.

1. Releia o briefing (requisitos + rubrica). Escolha: compute, banco, edge, IaC, CI/CD.
2. Desenhe o **diagrama**: VPC/subnets/AZs (se houver), componentes, fluxo de uma requisição de
   redirect, fluxo do deploy. Inclua onde vivem logs, métricas, backups e secrets.
3. Escreva 3–5 **mini-ADRs** (decisões de arquitetura): "Escolhi X em vez de Y porque… aceito o
   trade-off…". Ex.: DynamoDB vs. RDS; ASG vs. Lambda; com ou sem NAT/CloudFront.
4. Monte a **estimativa** no Pricing Calculator (Módulo 17) para ~30 dias do seu design + um
   cálculo próprio do custo pros dias do projeto. Salve o link/CSV.

### ✅ Marco da Fase 1 → Design Review
Apresente ao Claude: diagrama + ADRs + estimativa. Ele vai fazer o **design review** — perguntas
do tipo "cadê o SPOF?", "o que cai junto com a AZ a?", "por que essa peça existe?". Ajuste o que
for derrubado. **Só passe para a Fase 2 com o design aprovado.**

---

## Fase 2 — Fundação: rede + dados via IaC (💵 começa a custar — o quê, depende do design)

**Objetivo:** a base que não muda: rede (se houver), camada de dados, backup — tudo em código.

1. Inicie o **repositório**: estrutura de IaC (Módulo 11), `.gitignore` (state/secrets/tfvars!),
   README com `apply`/`destroy`. Considere state remoto (S3) se usar Terraform.
2. Provisione via IaC: VPC/subnets em 2+ AZs (se seu design usa), SGs mínimos, a **camada de
   dados** (tabela DynamoDB *ou* RDS Multi-AZ) e os secrets (Secrets Manager/SSM) — nada de senha
   em código ou state versionado.
3. Configure **backup desde já** (Módulo 18): PITR no DynamoDB *ou* backups automáticos no RDS /
   plano no AWS Backup por tag. Backup é fundação, não enfeite final.
4. Rode `apply`, confira no console, rode `destroy`, rode `apply` de novo. **Reproduzível?**
   Então é IaC de verdade.

### ✅ Marco da Fase 2
`apply` cria tudo do zero sem passos manuais; recursos taggeados `Projeto=capstone`; backup ativo;
zero secret no Git (mostre o `.gitignore` e o repo pro Claude). ⚠️ RDS Multi-AZ ligado cobra
~US$ 0,80/dia — se vai pausar o projeto por dias, pare/destrua.

---

## Fase 3 — App + compute (💵 ALB ~US$ 0,60/dia + instâncias, se aplicável)

**Objetivo:** a aplicação no ar, **multi-AZ**, atrás de um ponto de entrada único.

1. Escreva a aplicação mínima (RF1–RF5). Teste **localmente** contra a camada de dados
   (credenciais temporárias/role — Módulo 02) antes de subir.
2. Provisione o compute **via IaC**: ALB + ASG (2+ AZs, launch template com user data) *ou*
   Lambda + API Gateway. Role do app com **least privilege real** (só a tabela/bucket dele).
3. Aponte o health check do ALB/target group pro **`/health`** (que toca o banco — RF5).
4. Valide de fora: criar link → redirect funciona → contador incrementa → `/stats` responde.

### ✅ Marco da Fase 3
`curl` de fora prova RF1–RF5 funcionando via ALB/endpoint; instâncias/execuções em 2+ AZs;
targets saudáveis; a role do app não tem `*`. Anote o custo/dia real que começou a correr.

---

## Fase 4 — CI/CD (💵 ~US$ 0; minutos de build no free tier)

**Objetivo:** push na branch principal → teste → deploy, sem mão humana.

1. Monte o pipeline (Módulo 16: GitHub Actions ou CodePipeline/CodeBuild): etapa de **teste**
   (mesmo básica) e etapa de **deploy** (atualizar launch template/instance refresh, deploy da
   Lambda, ou o que seu design pedir).
2. Autenticação do pipeline→AWS com **role** (OIDC no GitHub Actions), **jamais** access keys
   coladas em secrets se OIDC for possível — e nunca no código.
3. Prove o ciclo: mude algo visível (ex.: versão no `/health`), push, acompanhe o pipeline,
   confira a mudança no ar **sem downtime** (o ALB segurou as pontas?).

### ✅ Marco da Fase 4
Histórico do pipeline mostrando: push → verde → mudança no ar. Rollback documentado no README
(nem que seja "revert + push"). O Claude vai pedir pra ver o histórico.

---

## Fase 5 — Observabilidade + alarmes (💵 ~US$ 0,20/alarme/mês; dashboards free tier)

**Objetivo:** enxergar o sistema e ser avisado antes do usuário reclamar.

1. **Dashboard** (Módulo 12) com as métricas-chave do SEU design — ex.: requests e 5xx do ALB,
   healthy hosts, latência p95, CPU do ASG, throttles/erros de Lambda/DynamoDB.
2. **Logs** da aplicação no CloudWatch Logs com **retenção definida** (ex.: 7–30 dias — Módulo 17
   mandou lembranças).
3. **≥ 2 alarmes acionáveis** → SNS → seu e-mail. Sugestões: `5xx > N por 5 min`,
   `HealthyHostCount < 2`, erros de função, orçamento (já existe da regra de custo).
4. **Teste um alarme de verdade**: provoque a condição (ex.: derrube o app numa instância,
   force 5xx) e receba o e-mail. Alarme nunca disparado é fé, não observabilidade.

### ✅ Marco da Fase 5
Dashboard aberto respondendo "o sistema está bem?" em 10 segundos; print do e-mail de alarme
recebido no teste provocado.

---

## Fase 6 — Teste de falha & recuperação (o exame prático de HA/DR)

**Objetivo:** provar os RNFs de resiliência **observando**, não torcendo. Peça ao Claude o
cenário oficial — o padrão é:

1. **Falha de instância/AZ:** com o dashboard aberto, termine (via console/CLI) uma instância do
   ASG — ou, se serverless, o Claude propõe um equivalente (ex.: forçar erros e observar
   alarme+recuperação). Meça: o serviço continuou respondendo? Em quanto tempo o ASG repôs?
   O alarme disparou? Anote a linha do tempo.
2. **Recuperação de dados (RPO/RTO reais):** simule perda lógica (delete um item/registro
   "importante") e **restaure do backup** (PITR pra tabela nova / restore de snapshot) seguindo o
   seu **runbook**. Cronometre (RTO) e verifique o que voltou (RPO).
3. Atualize o **runbook** com o que aprendeu — a primeira versão nunca sobrevive intacta ao
   primeiro teste. 😄

### ✅ Marco da Fase 6
Linha do tempo da falha (injeção → detecção → recuperação) + RPO/RTO medidos e anotados no
runbook. O Claude fará o "post-mortem" com você.

---

## Fase 7 — 🔥 TEARDOWN TOTAL + retrospectiva (a nota final é a conta zerada)

**Objetivo:** desmontar TUDO e provar. O teardown é parte da rubrica — recursos esquecidos
reprovam. 😉

1. **Antes de destruir:** colete as evidências dos entregáveis (prints do dashboard, histórico do
   pipeline, custo real no Cost Explorer vs. estimativa).
2. `terraform destroy` (ou delete das stacks) — o grosso deve morrer **pelo IaC**.
3. **Caça manual ao que o IaC não cobre** (checklist de caça, via console E CLI):
   - [ ] Instâncias EC2 / launch templates órfãos — `aws ec2 describe-instances`
   - [ ] Volumes `available` e **snapshots/AMIs** criados fora do IaC — `describe-volumes`, `describe-snapshots --owner-ids self`
   - [ ] ALBs/target groups — `aws elbv2 describe-load-balancers`
   - [ ] **NAT Gateways** e **EIPs** — `describe-nat-gateways`, `describe-addresses` (os vilões!)
   - [ ] RDS: instâncias E snapshots finais/manuais — `aws rds describe-db-instances / describe-db-snapshots`
   - [ ] DynamoDB: tabelas (inclusive a **restaurada na fase 6**!) — `aws dynamodb list-tables`
   - [ ] **Recovery points** no AWS Backup (plano deletado ≠ backups deletados) e o plano
   - [ ] Buckets S3 do projeto (inclusive o de state remoto, por último) — esvaziar versões antes
   - [ ] Log groups do projeto — `aws logs describe-log-groups`
   - [ ] Alarmes, dashboard e tópicos SNS — `aws cloudwatch describe-alarms`
   - [ ] Secrets no Secrets Manager (deleção agendada) e parâmetros SSM
   - [ ] Roles/policies IAM do projeto (app + pipeline) e OIDC provider, se criado
   - [ ] Certificados ACM / registros DNS / health checks, se criados
4. **Prova do zero:** amanhã, Cost Explorer filtrado por `Projeto=capstone` → custo do dia ≈ 0.
   O budget `capstone` pode ficar (gratuito) como sentinela por uns dias.
5. **Retrospectiva com o Claude:** estimativa vs. real, o que o design review salvou, o que o
   teste de falha ensinou, rubrica dimensão por dimensão.

### ✅ Marco da Fase 7
Checklist de caça 100% + evidência do custo zerando. **Projeto concluído — e o curso também.** 🎓

---

## ✅ Checklist de conclusão do módulo

- [ ] Fase 1: diagrama, ADRs e estimativa aprovados no design review.
- [ ] Fase 2: fundação 100% IaC, reproduzível (`destroy`+`apply`), backup ativo, sem secrets no Git.
- [ ] Fase 3: RF1–RF5 no ar, multi-AZ, least-privilege comprovado.
- [ ] Fase 4: push → deploy automático comprovado, rollback documentado.
- [ ] Fase 5: dashboard + logs com retenção + 2 alarmes (um disparado de verdade).
- [ ] Fase 6: falha injetada com linha do tempo; backup restaurado com RPO/RTO medidos.
- [ ] Fase 7: teardown total com checklist de caça + custo comprovadamente zerado.
- [ ] Runbook, estimativa vs. real e retrospectiva feitos.

---

## 🧪 Aplicação de teste da aula

O quiz deste módulo é uma **revisão geral do curso inteiro** — questões integradoras que cruzam
módulos (rede + compute + dados + operação). Rode:

```bash
python3 AWS/apps/modulo-19/quiz.py
```

Ele te faz perguntas sobre o curso todo e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, encare a **prova final** (`AWS/provas/modulo-19/`) —
12 cenários integradores, o "exame de formatura" do curso. Depois dela: a trilha de certificação
(`AWS/certificacoes/`) te espera. 🎓

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 19" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
