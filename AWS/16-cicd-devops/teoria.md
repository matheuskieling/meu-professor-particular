# Módulo 16 — CI/CD & DevOps (Teoria)

> Objetivo do módulo: entender a **cultura DevOps**, dominar os conceitos de **CI/CD** e as
> **estratégias de deploy**, conhecer a **suíte de CI/CD da AWS** (CodePipeline, CodeBuild,
> CodeDeploy) e — o caminho mais próximo do mercado — automatizar deploys com **GitHub Actions
> autenticando na AWS via OIDC**, sem nenhuma access key de longa duração. Ao final, um push no
> seu repositório vai publicar seu site sozinho.

---

## 1. DevOps: a cultura antes das ferramentas

**DevOps** não é um cargo nem uma ferramenta — é a cultura de **derrubar o muro** entre quem
desenvolve (Dev) e quem opera (Ops). No modelo antigo:

- Dev escreve código e "joga por cima do muro"; Ops sofre pra colocar em produção.
- Deploy é um **evento raro e traumático** (madrugada de sábado, checklist de 40 páginas, torcida).
- Quando quebra, começa o jogo de empurra: "funciona na minha máquina".

Com DevOps:

- O mesmo time **constrói e opera** ("you build it, you run it").
- Deploys são **pequenos, frequentes e chatos** (chato = bom: sem emoção, sem madrugada).
- **Automação em tudo**: build, teste, deploy, infra (IaC — módulo 11), observabilidade (módulo 12).
- Falhas viram **aprendizado** (post-mortem sem culpados), não caça às bruxas.

> 💡 O elo com o módulo 15: "mudanças pequenas, frequentes e reversíveis" é princípio do pilar de
> **excelência operacional**. CI/CD é a materialização técnica desse princípio. Por que funciona?
> Mudança pequena = raio de explosão pequeno + causa óbvia + rollback fácil. 100 deploys pequenos
> são mais seguros que 1 gigante.

---

## 2. CI vs. CD (e o outro CD)

Três termos parecidos, três coisas diferentes:

| Sigla | Nome | O que significa |
|-------|------|-----------------|
| **CI** | *Continuous Integration* | Todo push é **integrado** ao código principal com **build + testes automáticos**. Quebrou? O time fica sabendo em minutos, não na véspera do release. |
| **CD** | *Continuous **Delivery*** | Além do CI, todo build aprovado gera um artefato **pronto pra produção** — mas o deploy final tem um **botão/aprovação humana**. |
| **CD** | *Continuous **Deployment*** | Vai até o fim: passou nos testes, **entra em produção sozinho**, sem humano no circuito. |

**Pipeline** é a esteira que implementa isso: uma sequência de **estágios**
(`source → build → test → deploy`), onde cada estágio só roda se o anterior passou.

> ⚠️ **Pegadinha de prova e de entrevista:** a diferença entre delivery e deployment é **a
> aprovação manual antes de produção**. Delivery = *pode* ir a qualquer momento (humano decide);
> Deployment = *vai* automaticamente.

---

## 3. Estratégias de deploy

Como trocar a versão que está no ar? Cada estratégia troca **risco × custo × velocidade**:

| Estratégia | Como funciona | Prós | Contras |
|------------|---------------|------|---------|
| **In-place / recreate** | Para a versão velha, sobe a nova **nas mesmas máquinas** | Simples, sem custo extra | **Downtime**; rollback lento (re-deploy) |
| **Rolling** | Substitui as instâncias **aos poucos** (ex.: 2 por vez) | Sem downtime, sem dobrar custo | Duas versões convivem durante a janela; rollback é "rolar de volta" |
| **Blue/green** | Sobe um ambiente **novo completo (green)** ao lado do velho (blue) e **vira o tráfego** de uma vez (DNS/ALB) | Rollback **instantâneo** (volta o tráfego pro blue); testa o green antes de virar | **Custo dobrado** durante a transição |
| **Canary** | Manda uma **fração** do tráfego (ex.: 5%) pra versão nova; métricas ok → aumenta até 100% | Menor raio de explosão; validação com tráfego **real** | Mais complexo (precisa de métricas boas e automação pra decidir) |

> 💡 Lembre do módulo 14: **Route 53 weighted routing** é um jeito de fazer canary entre ambientes;
> ALB com target groups ponderados é outro (mais fino). CodeDeploy automatiza blue/green e canary
> pra EC2, ECS e Lambda.

> ⚠️ Rolling e canary exigem que **duas versões convivam**: cuidado com migrações de banco
> incompatíveis (a v1 ainda está rodando enquanto a v2 entra!). Regra prática: mudanças de schema
> **retrocompatíveis** (expand → migrate → contract).

---

## 4. A suíte AWS: CodePipeline, CodeBuild, CodeDeploy

Três serviços que se encaixam (e podem ser usados separadamente):

### CodePipeline — o orquestrador
Modela a **esteira**: estágios (`Source → Build → Deploy`), ações em cada estágio, artefatos
passando de um pro outro (via S3), gatilho automático no push. Suporta **aprovações manuais**
entre estágios (o "botão" do continuous delivery).

- **Fontes:** GitHub (via CodeConnections), S3, ECR...
- 💵 **Custo:** o modelo atual (V2) cobra **por minuto de execução de ação** (100 min/mês grátis);
  pipelines antigos (V1) custam **US$ 1/mês por pipeline ativo** (o primeiro grátis). De qualquer
  forma: **teardown ao final da prática.**

### CodeBuild — o construtor
Executa **builds e testes** em containers efêmeros gerenciados. Você descreve os comandos num
**`buildspec.yml`** na raiz do repo:

```yaml
version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: 20
  build:
    commands:
      - npm ci
      - npm test
      - npm run build
artifacts:
  files:
    - "dist/**/*"
```

- Fases: `install → pre_build → build → post_build`; `artifacts` diz o que sai do build.
- 💵 **Free tier: 100 minutos de build/mês** (no tipo de instância pequeno padrão) — de sobra pra estudar.

### CodeDeploy — o implantador
Automatiza o **deploy** do artefato em **EC2/on-premises** (via agente instalado), **ECS**
(blue/green de task sets) ou **Lambda** (shift de tráfego entre versões, canary/linear). Você
descreve os passos num **`appspec.yml`**: onde copiar arquivos e quais **hooks** rodar
(`BeforeInstall`, `AfterInstall`, `ApplicationStart`, `ValidateService`...). Suporta rollback
automático se um alarme do CloudWatch disparar durante o deploy.

> 💡 Resumo pra memorizar: **Pipeline orquestra, Build constrói/testa, Deploy implanta.**
> (E o antigo CodeCommit — git gerenciado da AWS — foi **descontinuado para novos clientes em
> 2024**; o mercado e a própria AWS apontam pro GitHub/GitLab como fonte.)

---

## 5. A alternativa mainstream: GitHub Actions + OIDC

No mercado real, a combinação mais comum hoje é **GitHub Actions** (o CI/CD embutido no GitHub)
fazendo deploy **na AWS**. Workflows vivem em `.github/workflows/*.yml` e rodam em **runners**
gerenciados a cada evento (`push`, `pull_request`...). **Grátis para repositórios públicos**
(privados têm cota de 2.000 min/mês no plano free).

### O problema das access keys de longa duração

O jeito **errado** (e ainda comum): criar um IAM user, gerar access keys e colar nos *secrets* do
GitHub. Por que é ruim?

- A chave é **eterna**: vale até alguém lembrar de rotacionar (ninguém lembra).
- Vazou (log, fork malicioso, breach do repo) → acesso à sua conta **de qualquer lugar do mundo**.
- Viola o que aprendemos no módulo 02: **credenciais temporárias > permanentes, sempre**.

### O jeito certo: OIDC (OpenID Connect)

Com **OIDC**, o GitHub e a AWS estabelecem uma **confiança federada** — e **nenhum segredo é
armazenado em lugar nenhum**:

1. Você cadastra o GitHub como **Identity Provider OIDC** no IAM
   (`token.actions.githubusercontent.com`).
2. Cria uma **IAM role** cuja *trust policy* aceita tokens desse provider — **condicionada ao seu
   repositório/branch** (claim `sub`, ex.: `repo:voce/seu-repo:ref:refs/heads/main`).
3. No workflow, a action `aws-actions/configure-aws-credentials` pede um **token OIDC** ao GitHub
   (que **prova** "sou o job X do repo Y na branch Z"), troca-o via `sts:AssumeRoleWithWebIdentity`
   por **credenciais temporárias** (~1 h) e pronto.

Por que é melhor, ponto a ponto:

| | Access keys no secret | OIDC |
|---|---|---|
| Segredo armazenado | Sim (eterno, no GitHub) | **Nenhum** |
| Validade da credencial | Permanente | **~1 hora**, emitida por job |
| Se vazar | Acesso irrestrito até revogar | Token expira em minutos; inútil fora do contexto |
| Escopo | Onde a chave for usada | **Só o repo/branch** da trust policy |
| Rotação | Manual (ninguém faz) | Automática por natureza |

> ⚠️ **Detalhe que derruba gente:** na trust policy, a condição do claim `sub` deve ser **restrita**
> (`repo:SEU-USUARIO/SEU-REPO:*` no mínimo; ideal com branch). Um `sub` frouxo (`repo:*`)
> deixaria **qualquer repositório do GitHub** assumir sua role. Least privilege também na federação!

### Deploy de containers (visão)

O mesmo padrão serve pra **ECR + ECS** (módulo 09): o workflow builda a imagem Docker, faz push
pro **ECR** (login via OIDC), atualiza a *task definition* e chama o deploy no **ECS** (rolling do
próprio ECS ou blue/green via CodeDeploy). Actions oficiais: `amazon-ecr-login` e
`amazon-ecs-deploy-task-definition`.

### Aprovações e ambientes

O GitHub tem **Environments** (`staging`, `production`) com **required reviewers** — a versão
GitHub da aprovação manual do CodePipeline: o job de deploy em `production` **pausa até alguém
aprovar**. Além disso, cada environment pode ter seus próprios secrets/variáveis e a trust policy
OIDC pode ser restrita a um environment específico.

---

## 6. Glossário rápido do módulo

| Termo | Em uma frase |
|-------|--------------|
| DevOps | Cultura de unir dev e ops com automação e deploys pequenos e frequentes. |
| CI | Integrar todo push com build + testes automáticos. |
| Continuous Delivery | Artefato sempre pronto pra produção; deploy com aprovação humana. |
| Continuous Deployment | Passou nos testes, vai pra produção sem humano no circuito. |
| Pipeline | A esteira de estágios: source → build → test → deploy. |
| Rolling / blue-green / canary / in-place | Estratégias de troca de versão (risco × custo × velocidade). |
| CodePipeline / CodeBuild / CodeDeploy | Orquestra / constrói e testa / implanta. |
| buildspec.yml / appspec.yml | A receita do CodeBuild / a receita do CodeDeploy. |
| GitHub Actions | CI/CD do GitHub; workflows YAML em `.github/workflows/`. |
| OIDC | Federação GitHub→AWS: credenciais temporárias por job, **zero segredos armazenados**. |
| Trust policy | Quem pode assumir a role — no OIDC, restrita ao seu repo/branch. |
| Environment (GitHub) | Ambiente com secrets próprios e aprovação manual (required reviewers). |

---

## Checagem de entendimento

Antes de ir pra prática, tente responder (mentalmente ou pro Claude):

1. Qual a diferença entre **continuous delivery** e **continuous deployment**?
2. Sua app não pode ter downtime e o rollback precisa ser instantâneo; o orçamento aguenta dobrar
   a infra por 1 hora. Qual estratégia de deploy — e por quê não rolling?
3. Na suíte AWS, quem **orquestra**, quem **builda** e quem **implanta**? Onde vivem as "receitas" de cada um?
4. Por que OIDC é mais seguro que access keys nos secrets do GitHub? Cite 3 razões.
5. O que aconteceria se a trust policy da sua role OIDC tivesse o claim `sub` como `repo:*`?

Quando estiver confortável com essas respostas, siga para **`pratica.md`**.
