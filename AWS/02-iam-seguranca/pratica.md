# Módulo 02 — Conta, IAM & Segurança (Prática Guiada)

> Objetivo desta prática: colocar a mão na massa no IAM — criar **group + policy customizada**,
> criar um **user de teste** com privilégio mínimo, ver na pele um **AccessDenied**, criar e
> **assumir uma role** via STS, e fechar as travas de billing.
>
> **Abordagem:** Console primeiro (pra ver), CLI depois (pra fixar). Cada passo explica o *porquê*.
>
> ⏱️ Tempo estimado: 60–90 min. 💵 Custo: **US$ 0** — IAM, STS e Budgets são gratuitos.
> Nada nesta prática cria recurso pago.

---

## ⚠️ Antes de começar

- Você precisa do **Módulo 01 completo**: conta criada, user `admin-<seuNome>`, CLI configurada
  (`aws sts get-caller-identity` funcionando).
- Vamos criar identidades e chaves **de teste**. Como sempre: **nenhuma credencial entra no
  repositório** — só em `~/.aws/`.
- No teardown vamos apagar o user de teste e as chaves dele. Nada disso custa dinheiro, mas
  identidade órfã é sujeira de segurança.

---

## Parte A — Group + policy customizada (Console)

Cenário: você quer uma equipe "observadores de S3" que pode **listar e ler** buckets, e nada mais.

### Passo 1 — Criar a policy customizada
1. Console → **IAM** → **Policies** → **Create policy**.
2. Aba **JSON**, cole:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "SomenteLeituraS3",
         "Effect": "Allow",
         "Action": [
           "s3:ListAllMyBuckets",
           "s3:ListBucket",
           "s3:GetObject"
         ],
         "Resource": "*"
       }
     ]
   }
   ```
3. **Next** → Nome: `CursoS3SomenteLeitura` → **Create policy**.

> **Por quê:** essa é uma **customer managed policy** — reutilizável e versionada. Repare que
> demos só 3 ações de leitura. Sem `s3:PutObject`, sem `s3:DeleteObject`: least privilege.
> (`Resource: "*"` aqui é aceitável porque queremos ler *qualquer* bucket da conta; se fosse um
> bucket específico, usaríamos o ARN dele.)

### Passo 2 — Criar o group e anexar a policy
1. IAM → **User groups** → **Create group**.
2. Nome: `curso-observadores-s3`.
3. Em **Attach permissions policies**, busque e marque `CursoS3SomenteLeitura` → **Create group**.

### Passo 3 — Criar um user de teste e colocá-lo no group
1. IAM → **Users** → **Create user** → nome: `teste-leitor`.
2. **Não** marque acesso ao console (esse user é só pra CLI).
3. Em permissões, escolha **Add user to group** → marque `curso-observadores-s3` → crie.
4. Abra o user → **Security credentials** → **Create access key** → caso de uso **CLI** →
   copie o par de chaves (a secret aparece **uma vez**).

> ⚠️ Chaves de TESTE, mas o cuidado é o mesmo de sempre: nada de colar em arquivo do repo.
> Elas vão para um **profile separado** da CLI no próximo passo — e morrem no teardown.

---

## Parte B — Sentir o least privilege na pele (CLI)

### Passo 4 — Configurar um profile separado pra CLI
```bash
aws configure --profile teste-leitor
```
Cole as chaves do `teste-leitor`, região `us-east-1`, output `json`.

> **Por quê:** profiles permitem várias identidades na mesma máquina (`~/.aws/credentials` ganha
> uma seção `[teste-leitor]`). Seu profile padrão continua sendo o admin.

### Passo 5 — Confirmar quem você é em cada profile
```bash
aws sts get-caller-identity                          # deve mostrar admin-<seuNome>
aws sts get-caller-identity --profile teste-leitor   # deve mostrar user/teste-leitor
```

### Passo 6 — Testar o que o user PODE fazer
```bash
aws s3 ls --profile teste-leitor
```
> Deve funcionar (lista de buckets — possivelmente vazia, mas **sem erro**). É o
> `s3:ListAllMyBuckets` da policy em ação.

### Passo 7 — Testar o que o user NÃO PODE fazer
```bash
aws s3 mb s3://teste-negado-$RANDOM --profile teste-leitor
aws iam list-users --profile teste-leitor
```
> **Os dois devem falhar com `AccessDenied`** — e isso é o sucesso do exercício! Criar bucket
> exige `s3:CreateBucket` (não demos) e listar users exige `iam:ListUsers` (não demos nada de
> IAM). O que você está vendo é o **implicit deny**: tudo que não foi permitido, é negado.

> 💡 Guarde a sensação desse erro. `AccessDenied` não é "a AWS quebrou" — é o IAM trabalhando.
> O diagnóstico é sempre: *qual identidade fez a chamada? que policies ela tem? tem Allow pra
> essa ação nesse recurso? tem Deny explícito em algum lugar?*

---

## Parte C — Criar e assumir uma role (Console + CLI)

Agora o conceito mais importante do módulo na prática: **credenciais temporárias via STS**.

### Passo 8 — Criar a role (Console)
1. IAM → **Roles** → **Create role**.
2. Trusted entity type: **AWS account** → **This account**.
   > Isso gera a **trust policy**: "principals desta conta podem assumir esta role".
3. Permissões: busque e marque a policy **`AmazonEC2ReadOnlyAccess`** (AWS managed).
4. Nome: `curso-role-ec2-readonly` → **Create role**.
5. Abra a role criada e olhe a aba **Trust relationships** — leia o JSON. É uma policy cujo
   `Action` é `sts:AssumeRole` e o `Principal` é a sua conta.

### Passo 9 — Autorizar seu user a assumir a role
Seu user admin já pode (AdministratorAccess inclui `sts:AssumeRole`). Numa conta real, você
criaria uma policy mínima assim (só leia, não precisa criar agora):
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "sts:AssumeRole",
    "Resource": "arn:aws:iam::SUA_CONTA:role/curso-role-ec2-readonly"
  }]
}
```

### Passo 10 — Assumir a role via CLI
Descubra o número da sua conta e assuma:
```bash
aws sts get-caller-identity --query Account --output text    # anote o ID (12 dígitos)

aws sts assume-role \
  --role-arn arn:aws:iam::SUA_CONTA:role/curso-role-ec2-readonly \
  --role-session-name minha-sessao-teste
```
> A resposta traz `Credentials`: **AccessKeyId, SecretAccessKey, SessionToken e Expiration**
> (por padrão, 1 hora). São **credenciais temporárias** — repare que existe um `SessionToken`,
> coisa que access keys de user não têm, e uma data de expiração.

### Passo 11 — Usar as credenciais temporárias
Exporte as três (copie da resposta do passo anterior):
```bash
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

aws sts get-caller-identity
```
> O ARN agora mostra `...assumed-role/curso-role-ec2-readonly/minha-sessao-teste` — **você é a
> role**, não mais o seu user. Teste os limites dela:
```bash
aws ec2 describe-instances    # PERMITIDO (readonly de EC2)
aws s3 ls                     # NEGADO (a role não tem nada de S3)
```

### Passo 12 — Voltar a ser você
```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
aws sts get-caller-identity   # de volta ao admin-<seuNome>
```
> Variáveis de ambiente **têm precedência** sobre o `~/.aws/credentials` — por isso o `unset`
> é obrigatório, senão você fica "preso" na role até as credenciais expirarem.

---

## Parte D — Fechar as travas de billing (Console)

### Passo 13 — Liberar billing para users IAM (ação de root)
1. Logue como **root** (uma das raras ocasiões) → menu da conta → **Account**.
2. Seção **IAM user and role access to Billing information** → **Edit** → ative → salve.
3. Deslogue do root. De volta ao seu user admin, abra **Billing and Cost Management** e confirme
   que agora você enxerga as páginas de custo.

### Passo 14 — Conferir/afinar alertas
1. **Budgets**: confirme que o budget do M01 está lá; se quiser, adicione um de custo (US$ 5)
   com alerta em 80% do **previsto** (forecast).
2. **Billing preferences**: ative **Free Tier alerts** (e *Receive Billing Alerts*, se
   quiser criar alarmes CloudWatch de fatura depois).
3. Abra o **Cost Explorer** uma vez para habilitá-lo (leva umas horas pra popular).

---

## Parte E — Teardown (higiene de segurança)

Nada aqui custa dinheiro, mas **identidade de teste não fica pra trás**:

1. **Deletar as access keys do `teste-leitor`** (IAM → user → Security credentials), ou via CLI:
   ```bash
   aws iam list-access-keys --user-name teste-leitor
   aws iam delete-access-key --user-name teste-leitor --access-key-id AKIA...
   ```
2. **Remover o user do group e deletá-lo:**
   ```bash
   aws iam remove-user-from-group --user-name teste-leitor --group-name curso-observadores-s3
   aws iam delete-user --user-name teste-leitor
   ```
3. **Manter** (vamos reusar no curso): o group `curso-observadores-s3`, a policy
   `CursoS3SomenteLeitura` e a role `curso-role-ec2-readonly` — não custam nada e servem de
   referência. Se preferir apagar, ordem: desanexar policy → deletar group; deletar role.
4. Apague o profile de teste da CLI: edite `~/.aws/credentials` e remova a seção
   `[teste-leitor]` (e a correspondente em `~/.aws/config`).
5. Confirme que **não** ficou nenhuma variável `AWS_*` exportada no shell (`env | grep AWS_`).

---

## ✅ Checklist de conclusão do módulo

- [ ] Policy customizada `CursoS3SomenteLeitura` criada (e você entende cada campo do JSON).
- [ ] Group `curso-observadores-s3` criado com a policy anexada.
- [ ] User `teste-leitor` criado, no group, com profile próprio na CLI.
- [ ] Viu um comando **permitido** e dois **negados** (`AccessDenied`) e sabe explicar por quê.
- [ ] Role `curso-role-ec2-readonly` criada; leu a **trust policy** dela.
- [ ] Assumiu a role via `aws sts assume-role`, usou as credenciais temporárias e viu o ARN de
      `assumed-role`.
- [ ] Voltou ao seu user (`unset` das variáveis).
- [ ] Billing liberado para IAM users; Free Tier alerts ativos; Cost Explorer habilitado.
- [ ] Teardown: user e chaves de teste deletados; nenhuma variável AWS_ sobrando no shell.

---

## 🧪 Aplicação de teste da aula

Depois desta aula, rode o quiz interativo pra fixar o conteúdo:

```bash
python3 AWS/apps/modulo-02/quiz.py
```

Ele te faz perguntas sobre o que vimos e corrige na hora. Rode quantas vezes quiser.

Quando fechar o checklist e for bem no quiz, você está pronto pra **prova do módulo**
(`AWS/provas/modulo-02/`) e para o **Módulo 03 — Rede (VPC)**.

> 💡 **Dica:** peça pro Claude "vamos fazer o quiz do módulo 2" e ele conduz as perguntas aqui no
> chat, tirando suas dúvidas a cada questão. Você não precisa rodar nada sozinho.
