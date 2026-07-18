# Módulo 16 — CI/CD & DevOps (Prática Guiada)

> Objetivo desta prática: montar um **deploy automatizado de verdade**: a cada `git push`, o
> **GitHub Actions** builda e publica seu site no **bucket S3 do módulo 06** — autenticando na AWS
> via **OIDC, sem nenhuma access key armazenada**. Depois, um **caminho B demonstrativo** com a
> suíte nativa: um pipeline **CodePipeline → CodeBuild**.
>
> **Abordagem:** Console primeiro (pra ver cada peça), CLI/YAML depois (que é como CI/CD vive de
> verdade). Cada passo explica o *porquê*.
>
> ⏱️ Tempo estimado: 60–90 min. 💵 Custo: **US$ 0** no caminho principal (Actions grátis em repo
> público; S3 já existe). Caminho B: CodeBuild tem 100 min/mês grátis; **CodePipeline pode custar
> US$ 1/pipeline/mês (V1) após o primeiro grátis** — vamos criar e **apagar no teardown**.

---

## ⚠️ Antes de começar — leia isto

- **Pré-requisitos:** conta no **GitHub** (crie em <https://github.com/join> se não tiver — grátis)
  e o **bucket S3 do módulo 06**. Confirme os dois antes de seguir.
- Use um **repositório público** para o Actions ser 100% grátis (repos privados têm cota de
  2.000 min/mês, também suficiente).
- **Reforço do módulo 01/02:** em NENHUM momento vamos criar access keys pro GitHub. Se algum
  tutorial na internet mandar colar `AWS_SECRET_ACCESS_KEY` num secret — está **desatualizado**.
  Nosso caminho é OIDC.
- Anote seu **Account ID** (12 dígitos — `aws sts get-caller-identity`) e o **nome do bucket**;
  vamos usar nos dois caminhos.

---

## Parte A — Preparar o repositório no GitHub

### Passo 1 — Criar o repo e o site
1. GitHub → **New repository** → nome `meu-site-cicd` → **Public** → Create.
2. Na sua máquina:

```bash
mkdir meu-site-cicd && cd meu-site-cicd
git init -b main
cat > index.html <<'EOF'
<!doctype html>
<html lang="pt-br">
  <head><meta charset="utf-8"><title>CI/CD funcionando</title></head>
  <body><h1>Deploy v1 — publicado pelo GitHub Actions 🚀</h1></body>
</html>
EOF
git add . && git commit -m "site v1"
git remote add origin https://github.com/SEU-USUARIO/meu-site-cicd.git
git push -u origin main
```

---

## Parte B — Confiança OIDC: IAM Provider + Role (Console)

Aqui está o coração do módulo: ensinar a AWS a **confiar no seu repositório**.

### Passo 2 — Cadastrar o GitHub como Identity Provider
1. Console → **IAM** → **Identity providers** → **Add provider**.
2. Tipo: **OpenID Connect**.
3. **Provider URL:** `https://token.actions.githubusercontent.com` (clique em *Get thumbprint* se pedido).
4. **Audience:** `sts.amazonaws.com` → **Add provider**.

> **Por quê:** isso registra "tokens emitidos pelo GitHub Actions são um documento de identidade
> válido nesta conta". Ainda não dá permissão nenhuma — permissão vem da role, a seguir.

### Passo 3 — Criar a role com trust restrita ao SEU repo
1. IAM → **Roles** → **Create role** → **Web identity**.
2. **Identity provider:** `token.actions.githubusercontent.com` · **Audience:** `sts.amazonaws.com`.
3. **GitHub organization/username:** `SEU-USUARIO` · **repository:** `meu-site-cicd` (o assistente
   monta a condição do claim `sub` pra você).
4. Permissões: por enquanto **nenhuma policy gerenciada** — vamos criar uma inline mínima.
5. Nome: `gha-deploy-site` → **Create role**.
6. Abra a role → **Add permissions → Create inline policy** → JSON:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SyncNoBucket",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::SEU-BUCKET",
        "arn:aws:s3:::SEU-BUCKET/*"
      ]
    }
  ]
}
```

7. Confira a **trust policy** (aba *Trust relationships*) — ela deve conter:

```json
"Condition": {
  "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
  "StringLike":   { "token.actions.githubusercontent.com:sub": "repo:SEU-USUARIO/meu-site-cicd:*" }
}
```

> ⚠️ **Pare e leia o `sub`:** é ELE que garante que **só o seu repo** assume a role. Se estivesse
> `repo:*`, qualquer workflow de qualquer repositório do mundo entraria na sua conta. E repare na
> permission policy: a role só sabe fazer **sync nesse bucket** — se o token vazar, o estrago
> máximo é mexer nos arquivos do site. Least privilege de ponta a ponta.

---

## Parte C — O workflow de deploy (YAML)

### Passo 4 — Criar o workflow
No repo, crie `.github/workflows/deploy.yml`:

```yaml
name: Deploy site para o S3

on:
  push:
    branches: [main]

permissions:
  id-token: write   # necessário pro job pedir o token OIDC
  contents: read    # pro checkout

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configurar credenciais AWS (OIDC — sem secrets!)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::SEU-ACCOUNT-ID:role/gha-deploy-site
          aws-region: us-east-1

      - name: Sync para o bucket
        run: aws s3 sync . s3://SEU-BUCKET --delete --exclude ".git/*" --exclude ".github/*"
```

> Leia o YAML com calma:
> - `on.push.branches: [main]` — o gatilho: todo push na main.
> - `permissions.id-token: write` — **sem isso o OIDC não funciona** (o job não consegue pedir o
>   token). É o erro nº 1 de quem monta isso.
> - `role-to-assume` — nenhum secret: o job troca o token OIDC por credenciais temporárias de ~1 h.
> - `aws s3 sync --delete` — espelha o repo no bucket (removendo o que saiu do repo).

### Passo 5 — Push e primeira execução
```bash
git add .github && git commit -m "ci: workflow de deploy" && git push
```
1. GitHub → aba **Actions** → veja o workflow rodando → abra os logs de cada step.
2. No step de credenciais, repare: **nenhum secret usado** — só o ARN da role.
3. Verifique o resultado:

```bash
aws s3 ls s3://SEU-BUCKET/          # index.html atualizado agora
```

(Se a distribuição CloudFront do módulo 14 ainda existisse, você veria o site por ela; sem ela,
confirme pelo `aws s3 cp s3://SEU-BUCKET/index.html -` ou pelo console.)

### Passo 6 — O teste de verdade: mudar e ver publicar sozinho
1. Edite o `index.html` (troque para `Deploy v2 ...`).
2. `git commit -am "v2" && git push`.
3. Aba Actions → workflow roda → confira o objeto no S3 atualizado. **Isso é CI/CD:** você commitou,
   ninguém copiou arquivo pra lugar nenhum. 🎉

> 💡 **Quer sentir a segurança do OIDC?** Rode o workflow de novo e observe: cada execução recebe
> credenciais **novas e temporárias**. Não há nada pra rotacionar, nada pra vazar do repo.

---

## Parte D — Caminho B (demonstrativo): CodePipeline + CodeBuild

Agora a suíte nativa, pra você conhecer a "outra metade" do mercado (e das provas). Faremos o
mínimo que mostra a mecânica: **Source (S3) → Build (CodeBuild)**.

> 💵 **Custo:** CodeBuild → 100 min/mês grátis. CodePipeline → dependendo do tipo, **US$ 1/mês por
> pipeline (V1, primeiro grátis)** ou por minuto de ação (V2, 100 min grátis). Criaremos, veremos
> funcionar **e apagaremos no teardown**.

### Passo 7 — Bucket de fonte + artefato de exemplo
```bash
aws s3 mb s3://SEU-NOME-pipeline-source-$RANDOM   # anote o nome!

mkdir /tmp/app-demo && cd /tmp/app-demo
cat > buildspec.yml <<'EOF'
version: 0.2
phases:
  build:
    commands:
      - echo "Build rodou em $(date)"
      - echo "Testes passariam aqui"
artifacts:
  files:
    - "**/*"
EOF
echo "app de exemplo" > app.txt
zip -r app.zip buildspec.yml app.txt
aws s3 cp app.zip s3://SEU-BUCKET-SOURCE/app.zip
```

> CodePipeline com fonte S3 exige **versionamento** no bucket:
> `aws s3api put-bucket-versioning --bucket SEU-BUCKET-SOURCE --versioning-configuration Status=Enabled`

### Passo 8 — Criar o pipeline (Console)
1. Console → **CodePipeline** → **Create pipeline** (escolha a opção de build customizado).
2. Nome: `pipeline-demo` → role de serviço: **New service role**.
3. **Source:** provider **Amazon S3** → bucket de source → object key `app.zip`.
4. **Build:** provider **AWS CodeBuild** → **Create project**: nome `build-demo`, ambiente
   gerenciado padrão (Amazon Linux, instância pequena), buildspec: **Use a buildspec file**.
5. **Deploy:** **Skip deploy stage** (nossa demo termina no build).
6. **Create pipeline** → ele roda sozinho a primeira vez: veja **Source** ficar verde, depois
   **Build**; clique no build → **Logs** → ache o `Build rodou em ...`.

### Passo 9 — Disparar de novo (e entender a mecânica)
```bash
echo "mudou" >> app.txt && zip -r app.zip buildspec.yml app.txt
aws s3 cp app.zip s3://SEU-BUCKET-SOURCE/app.zip
```
Nova versão do objeto → o pipeline **dispara sozinho**. É o mesmo princípio do Actions: mudança na
fonte → esteira roda. Em produção, a fonte seria o GitHub (via CodeConnections) e haveria um
estágio de **Deploy** (CodeDeploy/ECS/S3) e possivelmente um de **aprovação manual**.

---

## 🔥 Parte E — Teardown (obrigatório)

O caminho principal (Actions + OIDC) **não custa nada** e pode ficar. O caminho B, não:

1. **CodePipeline:** Console → pipelines → `pipeline-demo` → **Delete** (⚠️ é ele que pode custar
   US$ 1/mês).
2. **CodeBuild:** projeto `build-demo` → **Delete build project** (não custa parado, mas higiene é
   higiene).
3. **Bucket de source:** esvaziar (inclusive **versões**, que o versionamento guarda) e remover:
   ```bash
   aws s3 rb s3://SEU-BUCKET-SOURCE --force
   ```
4. **Roles de serviço** criadas pelo assistente (`AWSCodePipelineServiceRole-...`,
   `codebuild-build-demo-...`): IAM → Roles → delete (não custam, mas limpe).
5. **Ficam de pé (decisão consciente):** o repo GitHub, o IdP OIDC, a role `gha-deploy-site` e o
   bucket do site — são gratuitos e formam seu pipeline pessoal. Se preferir zerar: delete a role e
   o identity provider no IAM.
6. Confira **Billing → Bills** nos próximos dias.

---

## ✅ Checklist de conclusão do módulo

- [ ] Conta GitHub OK e repo `meu-site-cicd` criado com o site.
- [ ] Identity Provider OIDC do GitHub cadastrado no IAM.
- [ ] Role `gha-deploy-site` criada com **trust restrita ao seu repo** e **policy mínima no bucket**.
- [ ] Workflow `deploy.yml` com `permissions: id-token: write` e `role-to-assume` (zero secrets!).
- [ ] Push na main → Actions rodou → S3 atualizado (v1 e v2).
- [ ] Entendeu, lendo os logs, que cada execução usa credenciais temporárias novas.
- [ ] Caminho B: pipeline S3 → CodeBuild criado, executado e **entendido** (buildspec, artefatos, gatilho).
- [ ] 🔥 **Teardown:** pipeline e projeto de build deletados, bucket de source removido.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-16/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-16/`) e para o **Módulo 17 — Otimização de Custos (FinOps)**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 16" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
